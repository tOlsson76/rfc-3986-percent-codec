"""Core percent-encoding and decoding logic for RFC 3986."""

from __future__ import annotations

from typing import Final

# The unreserved set (RFC 3986 §2.3): characters that have no special meaning
# and SHOULD be left unencoded.
UNRESERVED: Final[frozenset[str]] = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)

# General delimiters (RFC 3986 §2.2): the characters that give a URI its
# top-level syntactic structure. Only one of these should be considered "safe"
# at a time, depending on which component is being encoded.
GENDELIMS: Final[frozenset[str]] = frozenset(":/?#[]@")

# Sub-delimiters (RFC 3986 §2.2): characters that are meaningful within
# individual components but are not top-level delimiters.
SUBDELIMS: Final[frozenset[str]] = frozenset("!$&'()*+,;=")

# The full reserved set (RFC 3986 §2.2): gen-delims ∪ sub-delims.
RESERVED: Final[frozenset[str]] = frozenset(":/?#[]@!$&'()*+,;=")


class EncodingError(ValueError):
    """Raised when input cannot be percent-encoded."""


class DecodingError(ValueError):
    """Raised when a percent-encoded string cannot be decoded."""


class PercentCodec:
    """Percent-encodes and decodes strings per RFC 3986.

    The codec operates on :class:`str` input. The :meth:`encode` method
    returns a :class:`str` of US-ASCII characters (unreserved chars plus
    ``%XX`` sequences). The :meth:`decode` method reverses this, returning
    a :class:`str`.

    Parameters
    ----------
    safe:
        An iterable of single-character strings that must never be
        percent-encoded. By default no characters are safe beyond those
        enforced by this codec (only ASCII characters are emitted).
        ``safe`` is converted to a :class:`frozenset`; characters in ``safe``
        that are not ASCII will not appear in the output because they are
        passed through only if they are ASCII.
    plus_as_space:
        If ``True``, the ``+`` character is decoded as a space (U+0020) and
        spaces are encoded as ``+``. This is NOT standard RFC 3986 behavior;
        it is an ``application/x-www-form-urlencoded`` convention.
        The default is ``False``, which is RFC 3986-conformant.
    """

    __slots__ = ("_safe", "_plus_as_space")

    def __init__(self, safe: "str | frozenset[str] | set[str] | None" = None,
                 *, plus_as_space: bool = False) -> None:
        if safe is None:
            self._safe: frozenset[str] = frozenset()
        elif isinstance(safe, str):
            # Each character of the string is an individual safe character.
            self._safe = frozenset(safe)
        else:
            self._safe = frozenset(safe)
        self._plus_as_space = bool(plus_as_space)

    # ----------------------------------------------------------------- #
    # Encoding
    # ----------------------------------------------------------------- #

    def encode(self, value: str) -> str:
        """Percent-encode ``value`` per RFC 3986.

        Every byte of the UTF-8 representation of each character is emitted
        as ``%XX`` unless the character is ASCII and unreserved or in
        ``safe``. Encoding in terms of UTF-8 bytes (not Unicode code points)
        is the convention mandated by RFC 3986 §2.5 for non-ASCII characters.
        """
        if not isinstance(value, str):
            raise EncodingError(f"expected str, got {type(value).__name__}")

        out: list[str] = []
        for ch in value:
            if self._plus_as_space and ch == " ":
                out.append("+")
                continue

            if ch in UNRESERVED or ch in self._safe:
                out.append(ch)
                continue

            # Non-ASCII and unsafe ASCII characters are encoded by their
            # UTF-8 byte sequence, each byte as %XX.
            for b in ch.encode("utf-8"):
                out.append("%{:02X}".format(b))

        return "".join(out)

    # ----------------------------------------------------------------- #
    # Decoding
    # ----------------------------------------------------------------- #

    def decode(self, value: str) -> str:
        """Percent-decode ``value`` per RFC 3986.

        Reverses :meth:`encode`. Percent-sequences are decoded as UTF-8.
        Incomplete or malformed sequences (lone ``%``, non-hex digits, or
        truncated sequences) raise :class:`DecodingError`.
        """
        if not isinstance(value, str):
            raise DecodingError(f"expected str, got {type(value).__name__}")

        out: list[str] = []
        bytes_acc: list[int] = []
        i = 0
        n = len(value)

        def flush() -> None:
            """Emit accumulated percent-encoded bytes as a UTF-8 string."""
            if bytes_acc:
                # The accumulated bytes came from %XX sequences only.
                # Decode strictly; invalid UTF-8 is a decoding error.
                out.append(bytes(bytes_acc).decode("utf-8"))
                bytes_acc.clear()

        while i < n:
            ch = value[i]

            if self._plus_as_space and ch == "+":
                flush()
                out.append(" ")
                i += 1
                continue

            if ch == "%":
                if i + 2 >= n:
                    raise DecodingError(
                        "truncated percent-encoded sequence"
                    )
                hex_str = value[i + 1 : i + 3]
                if not _is_hex_pair(hex_str):
                    raise DecodingError(
                        f"invalid percent-encoded sequence: %{hex_str}"
                    )
                bytes_acc.append(int(hex_str, 16))
                i += 3
                continue

            # A literal character. Any accumulated percent-bytes must be
            # flushed before emitting it to preserve ordering.
            flush()
            out.append(ch)
            i += 1

        flush()
        return "".join(out)


def _is_hex_pair(s: str) -> bool:
    """Return ``True`` iff ``s`` is exactly two hex digits."""
    return len(s) == 2 and all(c in "0123456789abcdefABCDEF" for c in s)
