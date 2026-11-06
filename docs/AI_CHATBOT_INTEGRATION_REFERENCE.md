# PrismLive AI Chatbot Integration

This is a drop-in Flask integration kit for the existing PrismLive project. It adds a floating Prism AI button and a Gemini-powered assistant without replacing the current live-chat layout or its Socket.IO messaging.

## Files
- `ai_chat.py` — Flask API endpoint `/api/ai-chat`
- `templates/partials/prism_ai_widget.html` — launcher, AI logo, panel, composer
- `static/css/prism-ai.css` — scoped responsive styles
- `static/js/prism-ai.js` — browser chat logic
- `.env.example` — environment-variable example

## 1. Copy the files into your existing project
Copy `ai_chat.py` into the same folder as `app.py`.
Copy `templates/partials/prism_ai_widget.html` into `templates/partials/`.
Copy `static/css/prism-ai.css` into `static/css/`.
Copy `static/js/prism-ai.js` into `static/js/`.

If these folders already exist, merge the files; do not replace your existing CSS or JavaScript.

## 2. Register the blueprint in `app.py`
Add these lines after creating your Flask `app = Flask(__name__)` object:

```python
from ai_chat import ai_chat_bp
app.register_blueprint(ai_chat_bp)
```

Do not create a second Flask app. Keep your existing login, database, Socket.IO, and routes.

## 3. Add the widget to your existing live-chat template
At the bottom of the template that renders the screenshot's live chat container, immediately before `</body>`, add:

```jinja2
{% include "partials/prism_ai_widget.html" %}
```

The launcher is fixed near the bottom-right, above the usual message composer/send area. If it overlaps your existing Send button, change `bottom:105px` in `.prism-ai-launch-wrap` and `bottom:174px` in `.prism-ai-panel` in `static/css/prism-ai.css`.

## 4. Install dependencies
Activate your existing virtual environment, then run:

```bash
pip install requests python-dotenv
```

Or merge `requests>=2.31.0` and `python-dotenv>=1.0.0` into your current `requirements.txt` and install with `pip install -r requirements.txt`.

## 5. Get and configure the Gemini API key
1. Open Google AI Studio: https://aistudio.google.com/
2. Create an API key for the Gemini API.
3. Set `GEMINI_API_KEY` in your local environment. For local development, you can use a `.env` file and load it near the top of `app.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

4. Put your actual key in `.env` (not in JavaScript, HTML, GitHub, or screenshots).
5. Add `.env` to `.gitignore`.

For Render: open your service → Environment → Add Environment Variable:
- Key: `GEMINI_API_KEY`
- Value: your private API key
- Optional key: `GEMINI_MODEL`, value: `gemini-3.5-flash`

Save changes and redeploy. Use a model currently available to your API key/account if the default model is unavailable.

## 6. Run locally
```bash
python app.py
```
Open your existing local site, sign in as usual, and click the Prism AI sparkle button. The widget calls your own Flask backend; the API key never goes to the browser.

## 7. Test and troubleshoot
- `503 AI is not configured`: add `GEMINI_API_KEY` to the environment used by the running server.
- `502 Could not connect`: check Render/server logs, API key validity, model availability, and network access.
- `404 /api/ai-chat`: blueprint registration did not run or the app was not restarted.
- Widget not visible: verify the include is in the actual live-chat template and browser devtools has no missing static-file 404s.
- Widget overlaps Send: adjust the `bottom` values in the CSS as described above.
- Keep the existing Socket.IO chat and AI assistant as separate features. The AI assistant does not automatically read private messages, user accounts, or database records.

## Security notes
- Never put the API key in frontend code or commit `.env`.
- For public production deployments, add rate limiting, monitoring, and authentication/CSRF protections appropriate to your app.
- This starter does not save AI conversations to your database; history exists in the open browser widget only.
- The AI is not connected to bookings, account actions, or private user data unless you explicitly build and secure those integrations.
