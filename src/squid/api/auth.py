"""Authentication management for YouTube Music."""

from __future__ import annotations

import hashlib
import json
import time
import webbrowser
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from squid.config import Config

log = structlog.get_logger()

# Supported browsers for cookie extraction (in order of preference)
SUPPORTED_BROWSERS = ["firefox", "chrome", "chromium", "brave", "edge", "opera", "vivaldi", "safari"]


class AuthError(Exception):
    """Authentication error."""
    pass


class AuthManager:
    """Manages YouTube Music authentication."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._browser_path = config.browser_auth_path

    @property
    def is_authenticated(self) -> bool:
        """Check if valid credentials exist."""
        if not self._browser_path.exists():
            return False
        try:
            content = self._browser_path.read_text().strip()
            if not content:
                return False
            data = json.loads(content)
            return "cookie" in {k.lower() for k in data.keys()}
        except (json.JSONDecodeError, KeyError):
            return False

    def get_ytmusic(self):
        """Get authenticated YTMusic instance."""
        from ytmusicapi import YTMusic

        if not self.is_authenticated:
            raise AuthError("Not authenticated. Run 'squid --auth' to authenticate.")

        return YTMusic(str(self._browser_path))

    def authenticate(self, browser: str | None = None) -> bool:
        """Extract cookies from browser and save for ytmusicapi."""
        log.info("Starting authentication")

        print("\n" + "=" * 60)
        print("YOUTUBE MUSIC AUTHENTICATION")
        print("=" * 60)
        print("""
This will extract your YouTube Music login from your browser.
Make sure you are logged into music.youtube.com first!
""")
        print("=" * 60)
        print("\nExtracting cookies from browser...")

        try:
            cookies = self._extract_cookies(browser)
            headers = self._cookies_to_headers(cookies)
            self._save_headers(headers)

            # Verify the auth works
            print("Verifying authentication...")
            if self._verify_auth():
                log.info("Authentication successful", path=str(self._browser_path))
                print("\n" + "=" * 60)
                print("Authentication successful!")
                print("=" * 60)
                return True
            else:
                raise AuthError("Authentication verification failed. Please make sure you're logged into YouTube Music.")

        except Exception as e:
            log.error("Authentication failed", error=str(e))
            raise AuthError(f"Authentication failed: {e}") from e

    def _extract_cookies(self, browser: str | None = None) -> dict[str, str]:
        """Extract YouTube cookies from browser."""
        from yt_dlp.cookies import extract_cookies_from_browser

        browsers_to_try = [browser] if browser else SUPPORTED_BROWSERS

        for browser_name in browsers_to_try:
            try:
                print(f"  Trying {browser_name}...")
                cookie_jar = extract_cookies_from_browser(browser_name)

                # Filter for YouTube cookies
                yt_cookies = {}
                for cookie in cookie_jar:
                    if ".youtube.com" in cookie.domain:
                        yt_cookies[cookie.name] = cookie.value

                if "__Secure-3PAPISID" in yt_cookies or "SAPISID" in yt_cookies:
                    print(f"  Found YouTube cookies in {browser_name}!")
                    return yt_cookies

            except Exception as e:
                log.debug(f"Could not extract from {browser_name}", error=str(e))
                continue

        raise AuthError(
            "Could not find YouTube login cookies in any browser. "
            "Please make sure you're logged into YouTube Music in your browser."
        )

    def _cookies_to_headers(self, cookies: dict[str, str]) -> dict:
        """Convert cookies dict to ytmusicapi header format."""
        # Only include essential cookies for auth (avoid 413 Request Too Large)
        essential_cookies = {
            "SAPISID", "__Secure-3PAPISID", "__Secure-1PAPISID",
            "SID", "__Secure-3PSID", "__Secure-1PSID",
            "HSID", "SSID", "APISID",
            "SIDCC", "__Secure-3PSIDCC", "__Secure-1PSIDCC",
            "__Secure-3PSIDTS", "__Secure-1PSIDTS",
            "LOGIN_INFO", "PREF",
            "VISITOR_INFO1_LIVE", "VISITOR_PRIVACY_METADATA",
        }

        filtered_cookies = {k: v for k, v in cookies.items() if k in essential_cookies}

        # Build cookie string
        cookie_str = "; ".join(f"{k}={v}" for k, v in filtered_cookies.items())

        # Find SAPISID for authorization header
        sapisid = cookies.get("SAPISID") or cookies.get("__Secure-3PAPISID")
        if not sapisid:
            raise AuthError("Could not find SAPISID cookie. Please make sure you're logged in.")

        # Generate SAPISIDHASH
        timestamp = int(time.time())
        auth_string = f"{timestamp} {sapisid} https://music.youtube.com"
        auth_hash = hashlib.sha1(auth_string.encode()).hexdigest()

        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.5",
            "content-type": "application/json",
            "x-goog-authuser": "0",
            "x-origin": "https://music.youtube.com",
            "origin": "https://music.youtube.com",
            "authorization": f"SAPISIDHASH {timestamp}_{auth_hash}",
            "cookie": cookie_str,
        }

        return headers

    def _save_headers(self, headers: dict) -> None:
        """Save headers to file."""
        self._browser_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._browser_path, "w") as f:
            json.dump(headers, f, indent=2)

    def _verify_auth(self) -> bool:
        """Verify that authentication works by making a test API call."""
        try:
            from ytmusicapi import YTMusic
            yt = YTMusic(str(self._browser_path))
            # Try a simple authenticated call
            result = yt.get_library_playlists(limit=1)
            return True
        except Exception as e:
            log.debug("Auth verification failed", error=str(e))
            return False

    def clear_credentials(self) -> None:
        """Remove stored credentials."""
        if self._browser_path.exists():
            self._browser_path.unlink()
            log.info("Credentials cleared")
            print("Credentials cleared.")
        else:
            print("No credentials to clear.")
