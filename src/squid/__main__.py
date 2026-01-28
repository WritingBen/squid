"""Entry point for Squid."""

import argparse
import sys

import structlog

from squid.config import get_config


def setup_logging(verbose: bool = False) -> None:
    """Configure structured logging."""
    import logging

    level = logging.DEBUG if verbose else logging.WARNING

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=level, format="%(message)s", stream=sys.stderr)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="squid",
        description="A CMUS-inspired terminal frontend for YouTube Music",
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Run authentication flow (opens browser for Google login)",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the API cache",
    )
    parser.add_argument(
        "--clear-auth",
        action="store_true",
        help="Clear stored authentication credentials",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if args.version:
        from squid import __version__
        print(f"squid {__version__}")
        return 0

    setup_logging(args.verbose)
    config = get_config()

    if args.clear_auth:
        from squid.api.auth import AuthManager
        auth = AuthManager(config)
        auth.clear_credentials()
        print("Authentication credentials cleared.")
        return 0

    if args.clear_cache:
        import asyncio
        from squid.api.cache import Cache
        cache = Cache(config.db_path)

        async def clear():
            await cache.clear()
            await cache.close()

        asyncio.run(clear())
        print("Cache cleared.")
        return 0

    if args.auth:
        from squid.api.auth import AuthManager, AuthError
        auth = AuthManager(config)
        try:
            auth.authenticate()
            print(f"Credentials saved to: {config.browser_auth_path}")
            return 0
        except AuthError as e:
            print(f"\nAuthentication failed: {e}", file=sys.stderr)
            return 1

    # Run the TUI application
    from squid.app import SquidApp
    app = SquidApp(config=config)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
