# Consent-based Single-Link Demo (Educational)

Purpose
- Educational demo to collect IP and optionally browser-provided geolocation only after explicit user consent.

Files
- server.py              — FastAPI server
- templates/consent.html — consent landing page
- /events                — admin JSON view of recorded, consented events

Run locally (Kali or any Linux)
1. Install dependencies:
   python3 -m pip install --user fastapi uvicorn httpx jinja2

2. Project layout:
   .
   ├─ server.py
   └─ templates/
      └─ consent.html

3. Start server:
   uvicorn server:app --reload --host 0.0.0.0 --port 8000

4. Create a link for testing (consenting participant):
   http://<your-ip-or-ngrok>/l/demo123

Expose to internet (only for consenting participants)
- Use ngrok: ngrok http 8000
- Share the ngrok URL + /l/<token> only with consenting people.

Important
- Do NOT use this to trick or capture data from people without consent.
- Secure /events and follow legal/privacy obligations before any public deployment.
