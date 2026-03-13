#!/usr/bin/env python3
"""
CSRF-aware login + access test for the "Daftar Permohonan Cuti" page.

Usage:
    python scripts/login_csrf_test.py
    python scripts/login_csrf_test.py --email admin@admin.com --password admin123

What it does:
    1. GET /login to retrieve CSRF token (from hidden input or meta tag).
    2. POST /login including the CSRF token.
    3. Inspect Set-Cookie headers and client cookie jar to confirm a session cookie is set.
    4. GET /cuti-v2/list and also request with Accept: application/json to see JSON error responses.
    5. Print helpful diagnostics to understand why "Gagal memuat halaman" might appear.

Notes:
    - This uses Flask's `app.test_client()` and runs inside the application context.
    - The script is conservative about parsing the CSRF token; it tries multiple strategies.
"""

import argparse
import re
import sys
from pprint import pformat

# Import the app (project root must be Python-importable)
try:
    from app import app
except Exception as e:
    print(
        "ERROR: Unable to import Flask app from project. Ensure you're running from project root."
    )
    print("Import exception:", e)
    sys.exit(2)


def extract_csrf_token(html):
    """
    Try multiple strategies to extract CSRF token from HTML:
    1. <input type="hidden" name="csrf_token" value="...">
    2. <input id="csrf_token" name="csrf_token" value="...">
    3. <meta name="csrf-token" content="...">
    4. Flask-WTF sometimes uses 'csrf_token' in a form field
    Returns token (str) or None.
    """
    if not html:
        return None

    # Strategy 1: hidden input name="csrf_token"
    m = re.search(
        r'<input[^>]+name=["\']csrf_token["\'][^>]+value=["\']([^"\']+)["\']', html
    )
    if m:
        return m.group(1)

    # Strategy 2: input with id
    m = re.search(
        r'<input[^>]+id=["\']csrf_token["\'][^>]+value=["\']([^"\']+)["\']', html
    )
    if m:
        return m.group(1)

    # Strategy 3: meta tag
    m = re.search(
        r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)["\']', html
    )
    if m:
        return m.group(1)

    # Strategy 4: any input named 'csrfmiddlewaretoken' (Django style)
    m = re.search(
        r'<input[^>]+name=["\']csrfmiddlewaretoken["\'][^>]+value=["\']([^"\']+)["\']',
        html,
    )
    if m:
        return m.group(1)

    return None


def show_cookie_jar(client):
    """
    Return a printable representation of cookies currently stored in the test client.
    This function is defensive across different Flask/test-client versions:
      - If `client.cookie_jar` exists and is iterable, return a list of cookie dicts.
      - Otherwise, try to extract 'Set-Cookie' headers from the last response (if available).
      - If neither is available, return a helpful message instead of raising.
    """
    cookies = []

    # Preferred path: inspect cookie_jar if present
    jar = getattr(client, "cookie_jar", None)
    if jar:
        try:
            for c in jar:
                cookies.append(
                    {
                        "name": getattr(c, "name", None),
                        "value": getattr(c, "value", None),
                        "domain": getattr(c, "domain", None),
                        "path": getattr(c, "path", None),
                        "secure": getattr(c, "secure", None),
                        "httponly": getattr(c, "httponly", None),
                        "expires": getattr(c, "expires", None),
                    }
                )
            return cookies
        except Exception:
            # Fall back to a repr of the jar if iteration/attributes fail
            try:
                return repr(jar)
            except Exception:
                pass

    # Fallback: try to inspect the most recent response headers for Set-Cookie
    # Some Flask test-client variants expose the last response as `client.response` or `client._last_response`.
    last_resp = getattr(client, "response", None) or getattr(
        client, "_last_response", None
    )
    if last_resp is not None:
        headers = getattr(last_resp, "headers", None)
        if headers:
            # headers.get_all is available on some header objects; otherwise fall back to get
            try:
                set_cookie_vals = headers.get_all("Set-Cookie")
            except Exception:
                sc = headers.get("Set-Cookie")
                set_cookie_vals = [sc] if sc else []
            return set_cookie_vals

    # Last resort: look for Set-Cookie header on the last returned response object if present on the client
    try:
        # Many test flows printed Set-Cookie on the immediate response; attempt to fetch it via the test client context
        return "No cookie_jar on client and no last response headers available to inspect cookies."
    except Exception:
        return "Unable to inspect cookies in this test-client environment."


def main(argv):
    ap = argparse.ArgumentParser(description="CSRF-aware login test for list_cuti_v2")
    ap.add_argument("--email", "-u", default="admin@admin.com", help="Login email")
    ap.add_argument("--password", "-p", default="admin123", help="Login password")
    ap.add_argument("--login-path", default="/login", help="Login URL path")
    ap.add_argument(
        "--target", default="/cuti-v2/list", help="Target URL to test after login"
    )
    ap.add_argument(
        "--follow",
        action="store_true",
        help="Follow redirects when testing final access",
    )
    args = ap.parse_args(argv)

    with app.test_client() as client:
        # Step 1: GET /login
        print("=" * 80)
        print("1) GET login page")
        print("=" * 80)
        resp = client.get(args.login_path)
        print("GET", args.login_path, "status:", resp.status_code)
        set_cookie_header = resp.headers.get("Set-Cookie")
        print("Set-Cookie header from GET /login:", set_cookie_header)
        html = resp.data.decode("utf-8", errors="ignore")
        token = extract_csrf_token(html)
        print("CSRF token found:", bool(token))
        if token:
            print(
                "CSRF token (truncated):",
                (token[:60] + "...") if len(token) > 60 else token,
            )
        else:
            # Show snippet to help debugging
            print("Login page snippet (first 800 chars):")
            print(html[:800])

        # Show session cookie name from config (if available)
        session_cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")
        print("Configured SESSION_COOKIE_NAME:", session_cookie_name)

        # Step 2: POST /login with token (if present)
        print("\n" + "=" * 80)
        print("2) POST login (including CSRF token if present)")
        print("=" * 80)

        data = {
            "email": args.email,
            "password": args.password,
        }
        if token:
            data["csrf_token"] = token

        # Some login forms may use 'remember' or other fields; include a common one
        data.setdefault("remember", "y")

        post_resp = client.post(args.login_path, data=data, follow_redirects=False)
        print("POST", args.login_path, "status:", post_resp.status_code)
        print("POST response headers (selected):")
        interesting_headers = {
            k: v
            for k, v in post_resp.headers.items()
            if k.lower() in ("set-cookie", "location", "content-type")
        }
        print(pformat(interesting_headers))

        # Show short snippet of response body
        try:
            body_snippet = post_resp.data.decode("utf-8", errors="ignore")[:1000]
        except Exception:
            body_snippet = repr(post_resp.data)[:1000]
        print("POST response body snippet:\n", body_snippet)

        if post_resp.status_code in (400, 401, 403):
            print(
                "Login POST returned a client error. This often indicates missing/invalid CSRF or wrong credentials."
            )
        elif post_resp.status_code == 302:
            print(
                "Login POST redirected (302). Location:",
                post_resp.headers.get("Location"),
            )
        elif post_resp.status_code == 200:
            print(
                "Login POST returned 200. Check response body for success/failure messages."
            )
        else:
            print("Login POST returned status", post_resp.status_code)

        # Show cookies stored in test client
        print("\nCookies currently in client.cookie_jar:")
        cookies = show_cookie_jar(client)
        print(pformat(cookies))

        # Check if the expected session cookie is present
        has_session_cookie = any(
            (isinstance(c, dict) and c.get("name") == session_cookie_name)
            or getattr(c, "name", None) == session_cookie_name
            for c in cookies
        )
        print("Session cookie present in jar?", has_session_cookie)

        # Step 3: Access target page after login
        print("\n" + "=" * 80)
        print("3) Access target page:", args.target)
        print("=" * 80)
        access_resp = client.get(args.target, follow_redirects=args.follow)
        print("GET", args.target, "status:", access_resp.status_code)
        if access_resp.status_code == 302:
            print("Redirected to:", access_resp.headers.get("Location"))
        # Print Content-Type and small body snippet
        print("Content-Type:", access_resp.headers.get("Content-Type"))
        try:
            access_body = access_resp.data.decode("utf-8", errors="ignore")
        except Exception:
            access_body = repr(access_resp.data)
        print("Body snippet (first 1000 chars):\n", access_body[:1000])

        # Heuristic: check for Indonesian expected title in HTML
        found_title = (
            "Daftar Permohonan Cuti" in access_body or "Daftar Cuti" in access_body
        )
        print("Found expected page title/text?", found_title)

        # Step 4: Try requesting Accept: application/json to see JSON error responses
        print("\n" + "=" * 80)
        print(
            "4) Access target with Accept: application/json (to get JSON error if any)"
        )
        print("=" * 80)
        json_resp = client.get(args.target, headers={"Accept": "application/json"})
        print("GET (Accept: application/json) status:", json_resp.status_code)
        ct = json_resp.headers.get("Content-Type", "")
        print("Content-Type:", ct)
        # Print JSON if any
        try:
            json_data = json_resp.get_json(silent=True)
        except Exception:
            json_data = None
        print("JSON body (if any):", pformat(json_data))

        # Final advice output
        print("\n" + "=" * 80)
        print("SUMMARY / NEXT STEPS")
        print("=" * 80)
        if found_title or (json_data and json_data.get("success") is True):
            print("SUCCESS: Target page appears accessible after login.")
            sys.exit(0)
        else:
            print("FAIL: Target page still not accessible.")
            print("Common causes to investigate:")
            print(
                "- CSRF token missing or not submitted (confirm the login form contains a hidden csrf_token field)."
            )
            print(
                "- Session cookie not being set or not sent back on subsequent requests (check domain, path, SameSite and Secure flags)."
            )
            print(
                "- Login form field names differ from 'email'/'password' (inspect the form and adjust payload)."
            )
            print("- You're hitting a different domain/port (cookie scope mismatch).")
            print(
                "- Reverse proxy or HTTPS misconfiguration causing cookies to be rejected."
            )
            print(
                "\nServer-side logs (Flask terminal) often show the exact error (e.g. 'The CSRF token is missing')."
            )
            sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
