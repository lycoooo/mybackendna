"""
server.py — local server para sa Netflix Trial Sender
-----------------------------------------------------
Sinisilbihan nito ang website (index.html / style.css / script.js) AT ang
/api/scan endpoint na kumukuha ng PH landing page ng Netflix na may kasamang
payload headers (mobile User-Agent + Cookie nfvdid/flwssn) — eksaktong gaya
ng ginagawa ng net.py. Kaya HINDI kailangan ng CORS proxy kapag ginagamit ito.

Paano patakbuhin:
    pip install httpx
    python server.py
    buksan ang http://localhost:8000
"""

import asyncio
import json
import sys
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

try:
    import httpx
except ImportError:
    print("Kulang ang 'httpx'. I-install ito:  pip install httpx")
    sys.exit(1)

if sys.platform == "win32":
    import os
    os.system("")  # para gumana ang kulay sa Windows console

HOST = "127.0.0.1"
PORT = 8000

LANDING_URL = "https://www.netflix.com/ph-en/"

DEFAULT_NFVDID = (
    "BQFmAAEBEHd71oHfkM7FU_oofLECV31AjKJNl9T0lBwR96xzXmWutUqrRdHCkAN1hcHjRlxLI8Eay"
    "T3bVFbyZDu8hLHeBXCz1dcwGebHrzm-7Ty5ckJTvQ%3D%3D"
)

GRAPHQL_URL = "https://web.prod.cloud.netflix.com/graphql"

RECAPTCHA_SITE_KEY = "6LdqW_EqAAAAAO87Fb_kcZfNzs0IqJRcKiJDYpUv"
INIT_QUERY_ID = "5d76d6a0-ccfe-4c31-b587-b4e1954732ca"
UPDATE_QUERY_ID = "0fd81de7-07af-4c7d-802f-0f4ea4181aa3"


def _headers_with_cookie(nfvdid, flwssn):
    """Kapareho ng headers na ginagamit ng net.py (may Cookie)."""
    return {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://www.netflix.com",
        "Referer": "https://www.netflix.com/",
        "Accept-Language": "en-US,en;q=0.9",
        "x-netflix.request.id": str(uuid.uuid4()),
        "x-netflix.request.toplevel.uuid": str(uuid.uuid4()),
        "x-netflix.request.clcs.bucket": "high",
        "x-netflix.context.form-factor": "phone",
        "x-netflix.context.app-version": "v38c5b0da",
        "x-netflix.context.locales": "en-in",
        "Cookie": f"nfvdid={nfvdid}; flwssn={flwssn}",
    }


async def check_banner(nfvdid, flwssn):
    """Kapareho ng TrialSender.check_banner() ng net.py — server-side."""
    headers = _headers_with_cookie(nfvdid, flwssn)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(LANDING_URL, headers=headers)

    text = resp.text
    if 'data-uia="free-trial-banner"' in text or "Try 30 days" in text:
        banner = ""
        marker = 'data-uia="free-trial-banner-text"'
        i = text.find(marker)
        if i != -1:
            j = text.find("</p>", i)
            if j != -1:
                banner = text[i:j].split(">", 1)[-1]
        return banner or "30-day trial"
    return None


def payload_init(email, flwssn):
    """CLCSWebInitSignup — kapareho ng net.py."""
    return {
        "operationName": "CLCSWebInitSignup",
        "variables": {
            "inputNode": "WELCOME",
            "locale": "en-IN",
            "inputFields": [
                {"name": "flwssn", "value": {"stringValue": flwssn}},
                {"name": "email", "value": {"stringValue": email}},
                {"name": "recaptchaError", "value": {"stringValue": "LOAD_TIMED_OUT"}},
                {"name": "recaptchaResponseTime", "value": {}},
                {"name": "recaptchaSiteKey", "value": {"stringValue": RECAPTCHA_SITE_KEY}},
                {"name": "recaptchaToken", "value": {}},
            ],
        },
        "extensions": {"persistedQuery": {"id": INIT_QUERY_ID, "version": 102}},
    }


def payload_update(email):
    """CLCSScreenUpdate — kapareho ng net.py."""
    return {
        "operationName": "CLCSScreenUpdate",
        "variables": {
            "format": "HTML",
            "imageFormat": "PNG",
            "locale": "en-IN",
            "serverState": "Bgjru+vcAxLTAf/qOOEwXPLVxW+7Jod9WpjYuKN8j1qfhQpzCK4mmQts5eMSeaP+l7s6NKcNBO4rmYabFFCVnMpCH3ib4AicvXAKm30Z+s5W3Cst0D0BK5x/pwn3QmByi/OgGwU/fzaiR5oxSlZe4fKVexWHISkE4GMzJqLaaXQR0M73ynZB9idNBfqsz3RA5WJN+DGAbVUOZlWl8eZqffvQpp/5MGubeQFpdwKqkAx1nHh7/xI1i9tDU0KLgrvkZrbe6nQ1MX2nc9TBxqnVVxtc3ptHdqydP1wlIu0YBiIOCgydgLg1SvK6tSPOff8=",
            "serverScreenUpdate": "Bgjru+vcAxKSAjDnHOxlaIbFSbwaWzZo/REHFnNG7OtpcXdKTDlcL4/o+huGi/fNW+jrqNDqDSsv1iytiG/ZtvO9ierUE9M1Kc/yEj9JsSiG3XpPciFDzPd6psSaG68XLbos+Qie0wniXCtJyWDLDuLd9ayCMB8qGCxwbov6B41kCQY/zArwlecm0GNoJdd5jvZfBJVtytD6mMCYnPA/9zhX4okj+6IGet9xOCYt76IDiuyESxgKbaOLcd6DQIDSBf4m/lYi2Tasj7olPkCaDIXxjU+0UY+b7eDyhvi2if2vt6510ARrGsSZq8DaazQmrpAbfiCW47s1/1mR59vUMYeT8VCqqAvbNwipqyP1DQMHtoTnCoWns0+x6IgYBiIOCgx9EW4i3i9SUswnHEg=",
            "inputFields": [
                {"name": "email", "value": {"stringValue": email}},
                {"name": "pipcConsent", "value": {"booleanValue": False}},
            ],
        },
        "extensions": {"persistedQuery": {"id": UPDATE_QUERY_ID, "version": 102}},
    }


async def send_signup(email, nfvdid, flwssn):
    """Kapareho ng TrialSender.send_signup() ng net.py — server-side,
    kasama ang totoong Cookie header (hindi kaya ng browser)."""
    headers = _headers_with_cookie(nfvdid, flwssn)
    async with httpx.AsyncClient(timeout=30) as client:
        resp1 = await client.post(GRAPHQL_URL, json=payload_init(email, flwssn), headers=headers)
        if '"errors"' in resp1.text.lower():
            return {"success": False, "step": 1,
                    "status1": resp1.status_code, "status2": None}
        resp2 = await client.post(GRAPHQL_URL, json=payload_update(email), headers=headers)
        if resp2.status_code == 200 and '"errors"' not in resp2.text.lower():
            return {"success": True, "step": 2,
                    "status1": resp1.status_code, "status2": resp2.status_code}
        return {"success": False, "step": 2,
                "status1": resp1.status_code, "status2": resp2.status_code}


class Handler(SimpleHTTPRequestHandler):
    """Sinisilbihan ang static files + ang /api/scan endpoint."""

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/scan":
            query = parse_qs(parsed.query)
            nfvdid = query.get("nfvdid", [DEFAULT_NFVDID])[0]
            flwssn = query.get("flwssn", [str(uuid.uuid4())])[0]
            try:
                banner = asyncio.run(check_banner(nfvdid, flwssn))
                self._json({"banner": banner})
            except Exception as e:  # noqa: BLE001
                self._json({"banner": None, "error": str(e)}, status=502)
            return
        if parsed.path == "/api/send":
            query = parse_qs(parsed.query)
            email = query.get("email", [""])[0]
            nfvdid = query.get("nfvdid", [DEFAULT_NFVDID])[0]
            flwssn = query.get("flwssn", [str(uuid.uuid4())])[0]
            if "@" not in email:
                self._json({"success": False, "step": 0,
                            "status1": None, "status2": None,
                            "error": "invalid email"}, status=400)
                return
            try:
                result = asyncio.run(send_signup(email, nfvdid, flwssn))
                self._json(result)
            except Exception as e:  # noqa: BLE001
                self._json({"success": False, "step": 0,
                            "status1": None, "status2": None,
                            "error": str(e)}, status=502)
            return
        super().do_GET()

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stdout.write("[server] " + fmt % args + "\n")


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"\n\u2705 Netflix Trial Sender server: http://{HOST}:{PORT}")
    print("   (static files: index.html, style.css, script.js)")
    print("   (/api/scan  — banner scan, gaya ng net.py)")
    print("   (/api/send  — trial signup, gaya ng net.py)")
    print("   (Ctrl+C para huminto)\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\u23f9 Huminto na ang server.")


if __name__ == "__main__":
    main()
