#!/usr/bin/env python3
"""
FitnessSyncer OAuth2 authorization code flow for MCP access.

Usage:
  python3 fitnesssyncer_oauth_authorization_flow.py --client-id ID --client-secret SECRET --redirect-uri URI

Opens the browser for the user to authorize, prompts for the redirect URL or
code, then exchanges for tokens and pretty-prints the result.
"""

import argparse
import json
import secrets
import sys
import urllib.parse
import urllib.request

AUTHORIZE_URL = "https://www.fitnesssyncer.com/api/oauth/authorize"
TOKEN_URL     = "https://www.fitnesssyncer.com/api/oauth/access_token"


def main():
    parser = argparse.ArgumentParser(description="FitnessSyncer OAuth2 authorization code flow")
    parser.add_argument("--client-id",     required=True, help="OAuth client ID")
    parser.add_argument("--client-secret", required=True, help="OAuth client secret")
    parser.add_argument("--redirect-uri",  required=True, help="Redirect URI registered with the client")
    parser.add_argument("--scope",         required=True, help="Scope of the Authorization")
    args = parser.parse_args()

    client_id     = args.client_id
    client_secret = args.client_secret
    redirect_uri  = args.redirect_uri
    scope         = args.scope

    state = secrets.token_urlsafe(16)

    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id":     client_id,
        "redirect_uri":  redirect_uri,
        "scope":         scope,
        "state":         state,
    })
    auth_url = f"{AUTHORIZE_URL}?{params}"

    print(f"\nOpen this URL in your browser to authorize:\n\n  {auth_url}\n")
    print("After authorizing, you will be redirected to a URL like:")
    print(f"  {redirect_uri}?code=XXXX&state=...\n")

    raw = input("Paste the full redirect URL (or just the code): ").strip()

    # Accept either the full redirect URL or just the code
    if raw.startswith("http"):
        parsed = urllib.parse.urlparse(raw)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        returned_state = qs.get("state", [None])[0]
        if returned_state and returned_state != state:
            print("WARNING: state mismatch — possible CSRF", file=sys.stderr)
    else:
        code = raw

    if not code:
        print("No code found.", file=sys.stderr)
        sys.exit(1)

    print("\nExchanging code for tokens...")
    post_data = urllib.parse.urlencode({
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  redirect_uri,
        "client_id":     client_id,
        "client_secret": client_secret,
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=post_data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code} from token endpoint:\n{body}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(f"Non-JSON response:\n{body}", file=sys.stderr)
        sys.exit(1)

    access_token  = data.get("access_token",  "(not present)")
    refresh_token = data.get("refresh_token", "(not present)")
    token_type    = data.get("token_type",    "")
    expires_in    = data.get("expires_in",    "")

    print("\n" + "-" * 60)
    print(f"  access_token:  {access_token}")
    print(f"  refresh_token: {refresh_token}")
    if token_type:
        print(f"  token_type:    {token_type}")
    if expires_in:
        print(f"  expires_in:    {expires_in}s")
    print("─" * 60)

    extra = {k: v for k, v in data.items()
             if k not in ("access_token", "refresh_token", "token_type", "expires_in")}
    if extra:
        print("\nOther fields:")
        print(json.dumps(extra, indent=2))


if __name__ == "__main__":
    main()