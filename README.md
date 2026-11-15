# Personal portfolio

A responsive, dark-and-green portfolio for a second-year Artificial Intelligence and Machine Learning student. The frontend is plain HTML, CSS, and JavaScript. The contact form is backed by a FastAPI API that validates submissions and sends them through Resend.

Personal details, institution, dates, email address, project names, descriptions, and skill lists are placeholders where indicated. Replace them with accurate information before publishing.

## Run locally

Requirements: Python 3.10+ and a modern browser.

1. Create and activate a virtual environment, then install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and set your Resend API key, verified sender address, and inbox address. Set `CORS_ORIGINS` to the exact origin serving the frontend.
3. Start the API from the project directory:

   ```powershell
   uvicorn main:app --reload --port 8000 --env-file .env
   ```

4. In a second terminal, serve the frontend from the project directory:

   ```powershell
   py -m http.server 5500
   ```

5. Open `http://localhost:5500`. In `config.js`, set `window.PORTFOLIO_API_URL` to `http://localhost:8000` to enable the form locally. The form stays disabled with a clear fallback message until an API URL is configured.

Health check: `http://localhost:8000/api/health`.

Run API tests with `pytest`.

## Contact email setup

Create a Resend account, verify a domain you control, and create an API key. Configure `RESEND_API_KEY`, `RESEND_FROM_EMAIL` (a sender on that verified domain), and `CONTACT_TO_EMAIL` in the backend environment. The API does not include credentials in its responses or logs. Never place the Resend API key in frontend code. The contact endpoint validates fields, rejects unexpected properties, uses a hidden honeypot field, and returns a service error if email delivery is not configured.

## Deployment

The site and API are separate deployable services. A static Vercel deployment serves the frontend files; it does not, by itself, run this FastAPI application as an ASGI server. Deploy the Python API to a Python host that supports ASGI (for example, Render, Railway, or Fly.io), then connect the two:

1. Deploy the repository's static frontend to Vercel using the project root, no build command, and `.` as the output directory (or use Vercel's static-site autodetection). The frontend needs no build step.
2. Deploy the FastAPI application separately on an ASGI-capable Python host. Use `pip install -r requirements.txt` for dependencies and `uvicorn main:app --host 0.0.0.0 --port $PORT` as the start command, adjusting the port expression to that host's convention.
3. Configure `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `CONTACT_TO_EMAIL`, and `CORS_ORIGINS` in the API host's secret/environment settings. `CORS_ORIGINS` must contain the exact deployed website origin, such as `https://your-site.vercel.app`, plus any custom domain origin you use.
4. Set `window.PORTFOLIO_API_URL` in `config.js` to the public API base URL (for example, `https://your-api.example.com`, without a trailing slash), and redeploy the static frontend. This file is public; only put the API's public base URL in it, never a secret.
5. Verify the API's `/api/health` endpoint and submit a test message from the deployed site. The Resend sender domain must be verified before delivery will succeed.

Use HTTPS for both deployed services. Do not configure wildcard CORS for a public contact API. If using a custom API host, confirm it supports the Python version and ASGI start command above.
