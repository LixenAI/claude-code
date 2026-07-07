"""
Pluggable publishing drivers. Each driver exposes:

    publish(post, brand, caption, video_abs_path) -> dict   # platform result

Raising MissingCredentials means "this platform isn't wired up yet" —
the publishing service then falls back to READY (manual posting from
the dashboard) instead of failing the post.
"""


class MissingCredentials(Exception):
    """Driver has no API credentials for this platform."""


class PublishError(Exception):
    """Publishing attempt failed (credentials were present)."""
