import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import functions_framework

import json
from google import genai
from google.genai import types

def get_gift_ideas():
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    serpapi_api_key = os.environ.get('SERPAPI_API_KEY')
    
    ideas = []
    if gemini_api_key:
        print("Using Gemini to generate specific gift ideas...")
        try:
            client = genai.Client(api_key=gemini_api_key)
            prompt = """You are an expert gift recommender. I need 3 specific, unique gift ideas for two women (Alyson, 29, and Lauryn, 26).
Cost strictly under $20 USD each.
Meaningful, interesting, or highly useful.
Must be actual physical items available on Amazon.
Return ONLY a valid JSON array of objects.
Each object must have exactly two keys: "name" (a specific, searchable product name, e.g., "Anker 313 Power Bank") and "reason" (a 1-sentence explanation of why it fits the criteria)."""
            
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            ideas = json.loads(response.text)
            print(f"Generated ideas from Gemini: {ideas}")
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            
    # Fallback curated list if Gemini fails or is not configured
    if not ideas or len(ideas) < 3:
        print("Falling back to curated gift ideas...")
        ideas = [
            {"name": "Tile Mate (2022) - Bluetooth Tracker", "reason": "Highly useful and practical for keeping track of keys, bags, and everyday items."},
            {"name": "Anker Portable Charger, 313 Power Bank", "reason": "A life-saver for keeping devices charged on the go. Meaningful through its sheer utility."},
            {"name": "Burt's Bees Hand Repair Gift Set", "reason": "While it skirts the line of 'lotions', this hand repair set is deeply useful for dry weather and stands out from generic bath bombs."}
        ]
        
    gifts = []
    if serpapi_api_key:
        print("Using SerpApi to search Amazon for the generated items...")
        for idea in ideas:
            params = {
                "engine": "google",
                "q": f"{idea['name']} site:amazon.com",
                "api_key": serpapi_api_key
            }
            try:
                response = requests.get("https://serpapi.com/search", params=params)
                response.raise_for_status()
                
                results = response.json().get('organic_results', [])
                found_match = False
                for res in results:
                    link = res.get("link", "")
                    if "amazon.com" in link:
                        price = res.get("rich_snippet", {}).get("top", {}).get("detected_extensions", {}).get("price")
                        if not price:
                            price = "Under $20"
                        elif isinstance(price, (int, float)):
                            price = f"${price}"
                            
                        gifts.append({
                            "name": idea["name"],
                            "reason": idea["reason"],
                            "price": str(price),
                            "link": link
                        })
                        found_match = True
                        break
                        
                if not found_match:
                     import urllib.parse
                     gifts.append({
                        "name": idea["name"],
                        "reason": idea["reason"],
                        "price": "Under $20",
                        "link": f"https://www.amazon.com/s?k={urllib.parse.quote(idea['name'])}"
                    })
            except Exception as e:
                print(f"Error calling search API for {idea['name']}: {e}")
                import urllib.parse
                gifts.append({
                    "name": idea["name"],
                    "reason": idea["reason"],
                    "price": "Under $20",
                    "link": f"https://www.amazon.com/s?k={urllib.parse.quote(idea['name'])}"
                })
    else:
        # If no search API, just return search links
        import urllib.parse
        for idea in ideas:
            gifts.append({
                "name": idea["name"],
                "reason": idea["reason"],
                "price": "Under $20",
                "link": f"https://www.amazon.com/s?k={urllib.parse.quote(idea['name'])}"
            })
            
    return gifts[:3]

@functions_framework.http
def gift_agent(request):
    """HTTP Cloud Function entry point."""
    print("Starting the gift finding agent...")
    
    sender_email = os.environ.get("SENDER_EMAIL", "your_email@gmail.com")
    receiver_email = os.environ.get("RECEIVER_EMAIL", "your_email@gmail.com")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    
    if not gmail_password:
        return ("Error: GMAIL_APP_PASSWORD is not set.", 500)
        
    gifts = get_gift_ideas()
    
    # Generate clean HTML content
    html_content = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
          h2 {{ color: #2c3e50; }}
          .gift-card {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
          .gift-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #34495e; }}
          .price {{ color: #27ae60; font-weight: bold; }}
          .reason {{ font-style: italic; color: #555; }}
          .button {{ display: inline-block; padding: 8px 15px; margin-top: 10px; background-color: #f0c14b; color: #111; text-decoration: none; border: 1px solid #a88734; border-radius: 3px; font-weight: bold; }}
          .button:hover {{ background-color: #dfae33; }}
        </style>
      </head>
      <body>
        <h2>Monthly Gift Ideas for Alyson & Lauryn</h2>
        <p>Here are 3 hand-picked gifts that are interesting, useful, and strictly under $20!</p>
    """
    
    for idx, gift in enumerate(gifts, 1):
        html_content += f"""
        <div class="gift-card">
          <div class="gift-title">{idx}. {gift['name']}</div>
          <p><strong>Estimated Price:</strong> <span class="price">{gift['price']}</span></p>
          <p class="reason"><strong>Why it fits:</strong> {gift['reason']}</p>
          <a href="{gift['link']}" class="button" target="_blank">View on Amazon</a>
        </div>
        """
        
    html_content += """
      </body>
    </html>
    """
    
    # Send the email using smtp
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Automated Gift Ideas for Alyson & Lauryn"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        # Connect to Gmail's SMTP server via SSL
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, gmail_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        
        print("Email sent successfully.")
        return ("Gift ideas sent successfully!", 200)
    except Exception as e:
        error_msg = f"Failed to send email: {e}"
        print(error_msg)
        return (error_msg, 500)
