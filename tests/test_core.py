"""Tests for :mod:`rfc_3986_percent_codec.core`.

Run with ``PYTHONPATH=src python -m unittest discover -s tests``.
"""

import unittest

from rfc_3986_percent_codec import (
    GENDELIMS,
    RESERVED,
    SUBDELIMS,
    UNRESERVED,
    DecodingError,
    EncodingError,
    PercentCodec,
)


class TestPredefinedSets(unittest.TestCase):
    """The predefined character sets must match RFC 3986 §2.2 and §2.3."""

    def test_unreserved_is_alnum_and_dash_dot_underscore_tilde(self) -> None:
        self.assertEqual(
            UNRESERVED,
            frozenset(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "abcdefghijklmnopqrstuvwxyz"
                "0123456789-._~"
            ),
        )

    def test_gendelims(self) -> None:
        self.assertEqual(GENDELIMS, frozenset(":/?#[]@"))

    def test_subdelims(self) -> None:
        self.assertEqual(SUBDELIMS, frozenset("!$&'()*+,;="))

    def test_reserved_is_union(self) -> None:
        self.assertEqual(RESERVED, GENDELIMS | SUBDELIMS)


class TestEncode(unittest.TestCase):
    """Encoding behavior."""

    def test_unreserved_characters_are_not_encoded(self) -> None:
        codec = PercentCodec()
        sample = "AZaz09-._~"
        self.assertEqual(codec.encode(sample), sample)

    def test_space_becomes_percent_20_by_default(self) -> None:
        # RFC 3986 does not special-case space; it is percent-encoded.
        self.assertEqual(PercentCodec().encode(" "), "%20")

    def test_space_becomes_plus_when_plus_as_space(self) -> None:
        self.assertEqual(PercentCodec(plus_as_space=True).encode(" "), "+")

    def test_ascii_punctuation_is_encoded_when_not_safe(self) -> None:
        codec = PercentCodec()
        self.assertEqual(codec.encode("!"), "%21")
        self.assertEqual(codec.encode("/"), "%2F")
        self.assertEqual(codec.encode("?"), "%3F")

    def test_safe_characters_are_preserved(self) -> None:
        codec = PercentCodec(safe="/!?")
        self.assertEqual(codec.encode("/!?"), "/!?")

    def test_unsafe_characters_in_safe_set_differ_from_default(self) -> None:
        # The default encodes ':'; with ':' safe it is preserved.
        self.assertEqual(PercentCodec().encode(":"), "%3A")
        self.assertEqual(PercentCodec(safe=":").encode(":"), ":")

    def test_non_ascii_is_utf8_percent_encoded(self) -> None:
        # U+00E9 (é) is two bytes in UTF-8: 0xC3 0xA9.
        self.assertEqual(PercentCodec().encode("é"), "%C3%A9")
        # U+20AC (€) is three bytes in UTF-8: E2 82 AC.
        self.assertEqual(PercentCodec().encode("€"), "%E2%82%AC")

    def test_empty_string_encodes_to_empty(self) -> None:
        self.assertEqual(PercentCodec().encode(""), "")

    def test_mixed_input(self) -> None:
        codec = PercentCodec(safe="/")
        self.assertEqual(codec.encode("a/b c"), "a/b%20c")

    def test_encode_rejects_non_str(self) -> None:
        with self.assertRaises(EncodingError):
            PercentCodec().encode(b"abc")  # type: ignore[arg-type]


class TestDecode(unittest.TestCase):
    """Decoding behavior."""

    def test_decode_reverses_simple_encoding(self) -> None:
        codec = PercentCodec()
        for s in ("hello", "a/b c", "é", "€", "!@#$%^&*()"):
            self.assertEqual(codec.decode(codec.encode(s)), s)

    def test_decode_percent_20_is_space(self) -> None:
        self.assertEqual(PercentCodec().decode("%20"), " ")

    def test_decode_plus_is_literal_plus_by_default(self) -> None:
        self.assertEqual(PercentCodec().decode("+"), "+")

    def test_decode_plus_as_space_when_configured(self) -> None:
        codec = PercentCodec(plus_as_space=True)
        self.assertEqual(codec.decode("a+b"), "a b")
        self.assertEqual(codec.decode(codec.encode("a b")), "a b")

    def test_decode_lowercase_hex_is_accepted(self) -> None:
        # Encoders SHOULD use uppercase, but decoders should be lenient.
        self.assertEqual(PercentCodec().decode("%c3%a9"), "é")

    def test_decode_mixed_case_hex_is_accepted(self) -> None:
        self.assertEqual(PercentCodec().decode("%C3%a9"), "é")

    def test_decode_truncated_sequence_raises(self) -> None:
        with self.assertRaises(DecodingError):
            PercentCodec().decode("%2")
        with self.assertRaises(DecodingError):
            PercentCodec().decode("%")

    def test_decode_invalid_hex_raises(self) -> None:
        with self.assertRaises(DecodingError):
            PercentCodec().decode("%GG")

    def test_decode_empty_returns_empty(self) -> None:
        self.assertEqual(PercentCodec().decode(""), "")

    def test_decode_rejects_non_str(self) -> None:
        with self.assertRaises(DecodingError):
            PercentCodec().decode(b"abc")  # type: ignore[arg-type]

    def test_decode_preserves_safe_literals_between_sequences(self) -> None:
        # Literal unreserved characters between percent-sequences must
        # remain intact.
        codec = PercentCodec()
        self.assertEqual(codec.decode("a%20b"), "a b")


class TestRoundTrip(unittest.TestCase):
    """Encoding and decoding are mutual inverses for varied inputs."""

    def test_round_trip_with_safe_set(self) -> None:
        codec = PercentCodec(safe="/?:@&=+$,")
        for s in ("/path/to/thing", "a:b@c", "x?y=z", "plain"):
            self.assertEqual(codec.decode(codec.encode(s)), s)

    def test_round_trip_plus_as_space(self) -> None:
        codec = PercentCodec(plus_as_space=True)
        for s in ("a b", "  ", "+", "a+b c"):
            self.assertEqual(codec.decode(codec.encode(s)), s)


if __name__ == "__main__":
    unittest.main()
