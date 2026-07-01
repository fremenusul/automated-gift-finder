import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import functions_framework
import json
import random
import datetime
from google import genai
from google.genai import types

# Optional GCS library
try:
    from google.cloud import storage
except ImportError:
    storage = None

# History file name
HISTORY_FILE = "gift_history.json"

# Dynamic monthly themes and guidelines
MONTHLY_THEMES = {
    1: {
        "theme": "Cozy Winter Wellness",
        "description": "Focus on high-quality self-care, relaxation, and warmth for cold winter days (e.g. heated eye masks, herbal tea samplers, plush slippers, bath therapy).",
        "examples": ["Heated Aromatherapy Eye Mask", "Organic Chamomile and Lavender Tea Sampler Set", "Cozy Fleece-lined Slipper Socks"]
    },
    2: {
        "theme": "Creative Hobbies & Mini-Crafts",
        "description": "Focus on beginner-friendly DIY kits, journaling, coloring, or custom hobbies to explore at home (e.g. embroidery kits, modern bullet journals, simple card games).",
        "examples": ["Embroidery Starter Kit for Beginners", "Dotted Bullet Journal with Stencils", "The Mind Card Game"]
    },
    3: {
        "theme": "Spring Refresh & Cozy Organization",
        "description": "Focus on clever organizers, home styling, fresh floral scents, and resetting the space (e.g. ceramic tray organizers, elegant drawer dividers, unique candle matches).",
        "examples": ["Ceramic Jewelry Tray with Gold Details", "Capri Blue Volcano Candle (Mini)", "Sleek Bamboo Drawer Dividers"]
    },
    4: {
        "theme": "Indoor Gardening & Green Living",
        "description": "Focus on plants, cute planters, gardening accessories, or eco-friendly reusables (e.g. self-watering pots, seed starter kits, reusable food wraps).",
        "examples": ["Geometric Ceramic Plant Pots (Set of 2)", "Microgreens Growing Kit", "Organic Beeswax Food Wraps (Pack of 3)"]
    },
    5: {
        "theme": "Travel & On-the-Go Essentials",
        "description": "Focus on packing tools, travel skincare, convenience accessories for road trips or vacations (e.g. travel packing cubes, refillable toiletries, tech cord organizers).",
        "examples": ["Compression Packing Cubes", "Refillable Travel Toiletries Bottles (Set of 4)", "Water-resistant Travel Cord Organizer Bag"]
    },
    6: {
        "theme": "Summer Hosting & Outdoor Picnics",
        "description": "Focus on picnic accessories, outdoor dining, summer drinks, or light travel items (e.g. folding picnic blankets, fancy drinkware, beach hair mists).",
        "examples": ["Waterproof Sand-free Picnic Blanket", "Aesthetic Ripple Glass Cups (Set of 2)", "Herbivore Coconut Ultra Hydrating Body Oil"]
    },
    7: {
        "theme": "Skincare & Summer Beauty Self-Care",
        "description": "Focus on hydration, cooling beauty tools, lip treatments, and relaxing summer self-care (e.g. ice rollers, glossy lip oils, calming face mists).",
        "examples": ["Facial Ice Roller for De-puffing", "Kopari Coconut Lip Glossy", "Rosewater Facial Spray with Aloe"]
    },
    8: {
        "theme": "Fun Cookery & Kitchen Gadgets",
        "description": "Focus on unique snacks/beverages, cute cooking accessories, baking tools, or gourmet salts/spices (e.g. matcha mixers, silicone baking mats, fancy seasoning blends).",
        "examples": ["Handheld Electric Milk Frother and Foam Maker", "Silicone Non-stick Baking Mats (Set of 2)", "Trader Joe's Everything Bagel Seasoning Set"]
    },
    9: {
        "theme": "Aesthetic Cozy Lighting & Ambiance",
        "description": "Focus on ambient lighting, candles, cozy room decor, or unique desk coasters (e.g. sunset lamps, cute matches, natural stone coasters).",
        "examples": ["Mini Sunset Projection Lamp", "Aesthetic Ceramic Ring Dish", "Genuine Slate Stone Coasters (Set of 4)"]
    },
    10: {
        "theme": "Autumn Cozy Reading & Warm Brews",
        "description": "Focus on reading accessories, tea/coffee organizers, cozy socks, and autumn vibes (e.g. book lights, mug warmers, specialty chai tea).",
        "examples": ["Rechargeable Clip-on Book Light", "Electric Mug Warmer for Desk", "Tazo Organic Chai Tea Concentrate"]
    },
    11: {
        "theme": "Board Games, Cozy Hosting & Party Games",
        "description": "Focus on engaging card/board games, serving dishes, holiday hosting prep, and interactive fun (e.g. party games, small serving platters, fun cheese knives).",
        "examples": ["Codenames Party Game", "Mini Acacia Wood Serving Board", "Stainless Steel Cheese Knife Set"]
    },
    12: {
        "theme": "Festive Cheer & Whimsical Stocking Stuffers",
        "description": "Focus on fun, whimsical winter items, holiday mugs, socks, and unique small surprises (e.g. holiday-themed socks, mini travel puzzles, gourmet hot cocoa).",
        "examples": ["Holiday-themed Novelty Socks", "Gourmet Hot Chocolate Gift Pack", "Mini Wooden Brain Teaser Puzzle"]
    }
}

# Extensive pool of fallback gifts to prevent duplicates in fallback scenario
FALLBACK_POOL = [
    {"name": "Laneige Lip Sleeping Mask", "reason": "A luxurious feeling lip mask that is highly rated and makes a great small gift."},
    {"name": "Dash Mini Maker Waffle Iron", "reason": "A super cute, fun, and highly practical mini kitchen gadget."},
    {"name": "Burt's Bees Hand Repair Gift Set", "reason": "Deeply useful for dry weather and stands out from generic bath bombs."},
    {"name": "CeraVe Hydrating Facial Cleanser", "reason": "A universally useful, highly-rated skincare staple."},
    {"name": "Gua Sha Facial Rejuvenation Tool", "reason": "A trendy self-care tool that promotes relaxation and skin health."},
    {"name": "Kitsch Satin Pillowcase", "reason": "A silky pillowcase that is gentle on hair and skin, adding a luxury feel to sleep."},
    {"name": "Baggu Reusable Shopping Bag", "reason": "An incredibly durable, chic, and packable bag for groceries or daily errands."},
    {"name": "Capri Blue Volcano Candle (Mini)", "reason": "Features an iconic, citrus-and-sugar scent that fills the room beautifully."},
    {"name": "Touchland Power Mist Hydrating Hand Sanitizer", "reason": "A stylish, moisturizing hand sanitizer spray that smells fantastic."},
    {"name": "Stasher Reusable Silicone Sandwich Bag", "reason": "An eco-friendly, durable silicone storage bag perfect for snacks or travel."},
    {"name": "Grace & Stella Under Eye Patches", "reason": "Fun gold foil under-eye masks that soothe puffiness and look great."},
    {"name": "Mario Badescu Facial Spray with Aloe & Rosewater", "reason": "A refreshing, hydrating face mist that is a staple for daily self-care."},
    {"name": "Wet Brush Original Detangler Hair Brush", "reason": "A cult-favorite detangling brush that is extremely gentle on wet hair."},
    {"name": "TonyMoly I'm Real Sheet Masks (Pack of 5)", "reason": "A fun assortment of popular Korean beauty masks for a spa night at home."},
    {"name": "Tree Hut Shea Sugar Scrub", "reason": "An exfoliating body scrub that smells amazing and leaves skin feeling silky smooth."},
    {"name": "Mighty Patch Original Acne Patch", "reason": "A highly practical and effective self-care item that is a must-have for skincare."},
    {"name": "REIDEA USB Rechargeable Electric Arc Lighter", "reason": "A modern, flameless electric lighter that is perfect for safely lighting candles."},
    {"name": "Cleverfy Aromatherapy Shower Steamers (6-pack)", "reason": "Transforms a regular shower into a relaxing spa-like aromatherapy experience."},
    {"name": "Zulay Kitchen Handheld Milk Frother", "reason": "A compact foam maker to easily elevate daily coffee or matcha into a cafe treat."},
    {"name": "The Original Makeup Eraser Cloth", "reason": "An eco-friendly reusable cloth that removes all makeup using only warm water."}
]

def get_history():
    bucket_name = os.environ.get("HISTORY_BUCKET")
    history_data = {"recommended_gifts": []}
    
    # Try GCS first if bucket is set and storage client is available
    if bucket_name and storage:
        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(HISTORY_FILE)
            if blob.exists():
                content = blob.download_as_text()
                history_data = json.loads(content)
                print(f"Loaded history from GCS bucket '{bucket_name}'.")
                return history_data
            else:
                print(f"History file '{HISTORY_FILE}' not found in GCS bucket '{bucket_name}'. Starting new history.")
        except Exception as e:
            print(f"Warning: Failed to load history from GCS: {e}. Falling back to local/memory.")
            
    # Local fallback
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history_data = json.load(f)
                print("Loaded history from local file.")
                return history_data
        except Exception as e:
            print(f"Warning: Failed to load local history file: {e}")
            
    # Ephemeral /tmp fallback (might persist in warm starts)
    tmp_path = os.path.join("/tmp", HISTORY_FILE)
    if os.path.exists(tmp_path):
        try:
            with open(tmp_path, "r") as f:
                history_data = json.load(f)
                print("Loaded history from /tmp.")
                return history_data
        except Exception as e:
            print(f"Warning: Failed to load /tmp history file: {e}")
            
    return history_data

def update_history(new_gifts):
    bucket_name = os.environ.get("HISTORY_BUCKET")
    history_data = get_history()
    
    # Append new gifts with current date
    today_str = datetime.date.today().isoformat()
    for gift in new_gifts:
        # Avoid duplicate entry logic in history list itself
        if not any(item["name"].lower() == gift["name"].lower() for item in history_data["recommended_gifts"]):
            history_data["recommended_gifts"].append({
                "name": gift["name"],
                "date": today_str
            })
            
    # Keep only the last 50 recommended gifts to avoid hitting token limits
    history_data["recommended_gifts"] = history_data["recommended_gifts"][-50:]
    
    # Try GCS first if bucket is set and storage client is available
    if bucket_name and storage:
        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(HISTORY_FILE)
            blob.upload_from_string(json.dumps(history_data, indent=2), content_type="application/json")
            print(f"Saved updated history to GCS bucket '{bucket_name}'.")
            return
        except Exception as e:
            print(f"Warning: Failed to save history to GCS: {e}. Falling back to local.")
            
    # Local save fallback
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history_data, f, indent=2)
            print("Saved updated history to local file.")
    except Exception as e:
        print(f"Warning: Failed to save history locally (e.g. read-only filesystem): {e}")
        
    # Always try writing to /tmp just in case
    try:
        tmp_path = os.path.join("/tmp", HISTORY_FILE)
        with open(tmp_path, "w") as f:
            json.dump(history_data, f, indent=2)
            print("Saved updated history to /tmp.")
    except Exception as e:
        print(f"Warning: Failed to save history to /tmp: {e}")

def select_fallback_gifts(history_gifts):
    history_names = {g["name"].lower() for g in history_gifts}
    available_fallbacks = [
        item for item in FALLBACK_POOL
        if not any(hist_name in item["name"].lower() or item["name"].lower() in hist_name for hist_name in history_names)
    ]
    # If too many are filtered out, just use the entire pool
    if len(available_fallbacks) < 5:
        available_fallbacks = FALLBACK_POOL
    
    selected = random.sample(available_fallbacks, min(5, len(available_fallbacks)))
    return selected

def get_gift_ideas(custom_theme=None, custom_desc=None):
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    serpapi_api_key = os.environ.get('SERPAPI_API_KEY')
    
    # Load history to feed as negative constraints
    history_data = get_history()
    past_gifts = history_data.get("recommended_gifts", [])
    past_names_str = ", ".join([f"'{g['name']}'" for g in past_gifts]) if past_gifts else "None"
    
    # Determine the theme
    current_month_num = datetime.date.today().month
    theme_info = MONTHLY_THEMES.get(current_month_num, {
        "theme": "Lifestyle & Wellness Refresh",
        "description": "Focus on high-quality self-care, relaxation, home cozy, or unique gadgets.",
        "examples": []
    })
    
    if custom_theme:
        theme_name = custom_theme
        theme_desc = custom_desc or "Focus on items fitting this theme."
        theme_examples = []
        print(f"Using custom theme override: '{theme_name}'")
    else:
        theme_name = theme_info["theme"]
        theme_desc = theme_info["description"]
        theme_examples = theme_info.get("examples", [])
        print(f"Using seasonal theme for month {current_month_num}: '{theme_name}'")
        
    ideas = []
    if gemini_api_key:
        print("Using Gemini to generate specific gift ideas...")
        try:
            client = genai.Client(api_key=gemini_api_key)
            
            month_name = datetime.date.today().strftime("%B")
            theme_examples_str = f"Theme Examples: {', '.join(theme_examples)}" if theme_examples else ""
            
            prompt = f"""Role: You are an expert personal shopper and trend analyst specializing in finding unique, non-work-related gifts for young professional women.
Task: Curate a list of 5 specific, highly-rated physical gift ideas for two women (Alyson, 29, and Lauryn, 26). Do NOT suggest office products, desk accessories, or work-related items.

Current Context:
Month: {month_name}
Theme for this month: {theme_name}
Theme Focus: {theme_desc}
{theme_examples_str}

Exclusions (Do NOT recommend any of these previously recommended items):
Past Gifts to Avoid: {past_names_str}
Anti-Patterns (Do NOT recommend): Laneige Lip Sleeping Mask, Dash Mini Maker Waffle Iron, Burt's Bees Hand Repair Gift Set, CeraVe Hydrating Facial Cleanser, Gua Sha Facial Rejuvenation Tool, bath bombs, cheap candles.

Constraints & Preferences:
Price: Strictly under $20 USD each.
Availability: Must be actual physical items readily available on Amazon.com.
Quality: Must be meaningful, interesting, or highly useful. Focus on lifestyle, home decor, self-care, beauty, kitchen gadgets, or quirky fun items.
Style: Girly items are totally fine, as long as they are unique and meaningful.
Specificity: Each suggestion must have a highly specific, searchable product name (e.g., "Aromatherapy Shower Steamers 12-pack" or "Kopari Coconut Lip Glossy" instead of just "lip balm" or "shower steamers") so it can be searched on Amazon.
Diversity: Make sure the 5 items cover a range of different concepts within the theme (e.g., do not suggest multiple items from the exact same sub-category like 5 face oils or 5 mugs).

Return ONLY a valid JSON array of objects.
Each object must have exactly two keys: "name" (a specific, searchable product name, e.g., "Laneige Lip Sleeping Mask") and "reason" (a 1-sentence explanation of why it fits the criteria)."""
            
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.9,
                ),
            )
            ideas = json.loads(response.text)
            print(f"Generated ideas from Gemini: {ideas}")
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            
    # Fallback curated list if Gemini fails or is not configured
    if not ideas or len(ideas) < 5:
        print("Falling back to curated gift ideas...")
        ideas = select_fallback_gifts(past_gifts)
        print(f"Fallback ideas selected: {ideas}")
        
    # Save the selected ideas to history
    try:
        update_history(ideas)
    except Exception as e:
        print(f"Error updating history: {e}")
        
    gifts = []
    if serpapi_api_key:
        print("Using SerpApi to search Amazon for the generated items in parallel...")
        import concurrent.futures
        import urllib.parse

        def search_idea(idea):
            params = {
                "engine": "google",
                "q": f"{idea['name']} site:amazon.com",
                "api_key": serpapi_api_key
            }
            try:
                response = requests.get("https://serpapi.com/search", params=params, timeout=10)
                response.raise_for_status()
                
                results = response.json().get('organic_results', [])
                for res in results:
                    link = res.get("link", "")
                    if "amazon.com" in link:
                        price = res.get("rich_snippet", {}).get("top", {}).get("detected_extensions", {}).get("price")
                        if not price:
                            price = "Under $25"
                        elif isinstance(price, (int, float)):
                            price = f"${price}"
                            
                        return {
                            "name": idea["name"],
                            "reason": idea["reason"],
                            "price": str(price),
                            "link": link
                        }
            except Exception as e:
                print(f"Error calling search API for {idea['name']}: {e}")
                
            return {
                "name": idea["name"],
                "reason": idea["reason"],
                "price": "Under $25",
                "link": f"https://www.amazon.com/s?k={urllib.parse.quote(idea['name'])}"
            }

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Run up to 5 searches concurrently
            results = list(executor.map(search_idea, ideas))
            gifts.extend(results)
    else:
        # If no search API, just return search links
        import urllib.parse
        for idea in ideas:
            gifts.append({
                "name": idea["name"],
                "reason": idea["reason"],
                "price": "Under $25",
                "link": f"https://www.amazon.com/s?k={urllib.parse.quote(idea['name'])}"
            })
            
    return gifts[:5]


@functions_framework.http
def gift_agent(request):
    """HTTP Cloud Function entry point."""
    print("Starting the gift finding agent...")
    
    sender_email = os.environ.get("SENDER_EMAIL", "your_email@gmail.com")
    receiver_email = os.environ.get("RECEIVER_EMAIL", "your_email@gmail.com")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    
    if not gmail_password:
        return ("Error: GMAIL_APP_PASSWORD is not set.", 500)
        
    # Parse potential custom theme override from JSON or args
    custom_theme = None
    custom_desc = None
    if request:
        try:
            request_json = request.get_json(silent=True)
            if request_json:
                custom_theme = request_json.get('theme')
                custom_desc = request_json.get('description')
            
            # Fallback to query arguments if JSON doesn't specify theme
            if not custom_theme and request.args:
                custom_theme = request.args.get('theme')
                custom_desc = request.args.get('description')
                
            if custom_theme:
                print(f"Custom theme override detected: '{custom_theme}'")
        except Exception as e:
            print(f"Failed to parse request JSON or parameters: {e}")
            
    gifts = get_gift_ideas(custom_theme=custom_theme, custom_desc=custom_desc)
    
    # Metadata for email headers
    month_name = datetime.date.today().strftime("%B")
    current_month_num = datetime.date.today().month
    display_theme = custom_theme if custom_theme else MONTHLY_THEMES.get(current_month_num, {}).get("theme", "Monthly Selection")
    
    # Generate clean HTML content
    html_content = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
          h2 {{ color: #2c3e50; margin-bottom: 5px; }}
          .subtitle {{ font-size: 16px; color: #7f8c8d; margin-top: 0; margin-bottom: 20px; }}
          .gift-card {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
          .gift-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #34495e; }}
          .price {{ color: #27ae60; font-weight: bold; }}
          .reason {{ font-style: italic; color: #555; }}
          .button {{ display: inline-block; padding: 8px 15px; margin-top: 10px; background-color: #f0c14b; color: #111; text-decoration: none; border: 1px solid #a88734; border-radius: 3px; font-weight: bold; }}
          .button:hover {{ background-color: #dfae33; }}
        </style>
      </head>
      <body>
        <h2>Monthly Gift Ideas for Alyson & Lauryn ({month_name})</h2>
        <div class="subtitle">Theme: <strong>{display_theme}</strong></div>
        <p>Here are 5 hand-picked gifts that are interesting, useful, and strictly under $20!</p>
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
    msg["Subject"] = f"Automated Gift Ideas ({month_name} - {display_theme})"
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
