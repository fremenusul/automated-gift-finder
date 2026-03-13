# Automated Gift Finder Agent

An automated gift-finding agent built as a Google Cloud Function (2nd Gen) in Python. This service curates specific, highly-rated physical gift ideas tailored to specific personas using Google's Gemini API and finds real product links on Amazon using SerpApi. The results are formatted and sent as an HTML email to a designated recipient.

## Features

- Uses **Gemini 2.5 Pro** to generate clever, non-generic gift concepts tailored to specific criteria.
- Uses **SerpApi** to search Amazon and retrieve actual links and estimated checking prices.
- Sends beautifully formatted HTML emails containing the gift recommendations.
- Designed to be easily deployable as an HTTP-triggered Google Cloud Function.

## Prerequisites

Before deploying or running this project, you will need:
- A Google Cloud Project with billing enabled.
- The following Google Cloud APIs enabled in your project:
  - **Cloud Functions API**
  - **Cloud Build API**
  - **Artifact Registry API**
  - **Cloud Run API**
  - **Cloud Logging API**
  - *(Optional)* **Vertex AI API** (if adapting the `google-genai` client for Vertex AI instead of Google AI Studio).
- A [Gemini API Key](https://aistudio.google.com/) for generating gift ideas.
- A [SerpApi API Key](https://serpapi.com/) for searching Amazon.
- A Gmail account with an **App Password** generated (for sending the emails via SMTP).

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/automated-gift-finder.git
   cd automated-gift-finder
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env.yaml` file in the root directory. **Do not commit this file to version control.** Add your actual secrets to this file format:
   ```yaml
   SENDER_EMAIL: "your_email@gmail.com"
   RECEIVER_EMAIL: "recipient_email@gmail.com"
   GMAIL_APP_PASSWORD: "your-16-character-app-password"
   SERPAPI_API_KEY: "your-serpapi-key"
   GEMINI_API_KEY: "your-gemini-key"
   ```

## Deployment to Google Cloud

This project is built to run natively as a Google Cloud Function. 

1. Install and authenticate with the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install).

2. Deploy the function using the following command (adjust region and runtime if desired):
   ```bash
   gcloud functions deploy gift-agent \
     --gen2 \
     --region=us-central1 \
     --runtime=python310 \
     --source=. \
     --entry-point=gift_agent \
     --trigger-http \
     --env-vars-file=.env.yaml
   ```
   *(Note: For production environments, consider using Google Cloud Secret Manager for handling sensitive keys instead of passing them in an env-vars-file)*

## Customization

You can dynamically change the gift-finding criteria by editing the AI prompt string inside `main.py` in the `get_gift_ideas()` function. Currently, it is configured with a strict budget of under $20 USD.
