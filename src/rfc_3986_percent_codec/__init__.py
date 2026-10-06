"""RFC 3986 percent-encoding codec for URIs.

A small, dependency-free library for percent-encoding and decoding
URI components per RFC 3986 with configurable safe character sets.

This module exposes the names documented in the README and tests:
    :class:`PercentCodec`
    :class:`EncodingError`
    :class:`DecodingError`
    :data:`UNRESERVED`
    :data:`RESERVED`
    :data:`SUBDELIMS`
    :data:`GENDELIMS`
"""

from .core import (
    GENDELIMS,
    RESERVED,
    SUBDELIMS,
    UNRESERVED,
    DecodingError,
    EncodingError,
    PercentCodec,
)

__all__ = [
    "PercentCodec",
    "EncodingError",
    "DecodingError",
    "UNRESERVED",
    "RESERVED",
    "SUBDELIMS",
    "GENDELIMS",
]
