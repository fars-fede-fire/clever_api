"""Exceptions for Clever API"""


class CleverError(Exception):
    """Generic Clever exception"""


class CleverConnectionError(CleverError):
    """Clever connection exception"""
