#!/usr/bin/env python3
"""
FitnessSyncer OAuth2 token refresh.

Usage:
  python3 fitnesssyncer_oauth_refresh_flow.py --client-id ID --client-secret SECRET --refresh-token TOKEN
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

TOKEN_URL = "https://www.fitnesssyncer.com/api/oauth/access_token"


def main():
    parser = argparse.ArgumentParser(description="FitnessSyncer OAuth2 token refresh")
    parser.add_argument("--client-id",     required=True, help="OAuth client ID")
    parser.add_argument("--client-secret", required=True, help="OAuth client secret")
    parser.add_argument("--refresh-token", required=True, help="Refresh token to exchange")
    args = parser.parse_args()

    post_data = urllib.parse.urlencode({
        "grant_type":    "refresh_token",
        "refresh_token": args.refresh_token,
        "client_id":     args.client_id,
        "client_secret": args.client_secret,
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
    print("-" * 60)

    extra = {k: v for k, v in data.items()
             if k not in ("access_token", "refresh_token", "token_type", "expires_in")}
    if extra:
        print("\nOther fields:")
        print(json.dumps(extra, indent=2))


if __name__ == "__main__":
    main()
