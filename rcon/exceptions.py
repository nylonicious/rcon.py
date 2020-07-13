"""rcon.py exceptions."""


__all__ = ("RCONException", "LoginFailure")


class RCONException(Exception):
    """Exception that's thrown when an RCON operation fails."""


class LoginFailure(RCONException):
    """Exception that's thrown when login function fails due to incorrect password."""
