"""Module entry point for launching the Deep Organizer GUI."""

from .gui import run_app


def main() -> int:
    """Delegate to the GUI runner."""
    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
