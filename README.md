# RFC 3986 Percent Codec

Percent-encodes and decodes URI components per RFC 3986, with configurable safe character sets and no dependencies beyond the Python standard library.

## Usage

```python
from rfc_3986_percent_codec import PercentCodec

# Default: strict RFC 3986. Nothing beyond unreserved characters is safe.
codec = PercentCodec()
codec.encode("a/b c")       # -> "a%2Fb%20c"
codec.decode("a%2Fb%20c")   # -> "a/b c"

# Preserve path separators when encoding a path component.
path_codec = PercentCodec(safe="/")
path_codec.encode("a/b c")  # -> "a/b%20c"

# application/x-www-form-urlencoded convention: '+' means space.
form_codec = PercentCodec(plus_as_space=True)
form_codec.encode("a b")    # -> "a+b"
form_codec.decode("a+b")    # -> "a b"
```

Exported names: `PercentCodec`, `EncodingError`, `DecodingError`, `UNRESERVED`, `RESERVED`, `GENDELIMS`, `SUBDELIMS`.

## Why this exists

The standard library's `urllib.parse.quote` mixes reserved-set handling with component-specific defaults, which makes its behavior surprising when reused across components. This library isolates one concern — byte-level percent-encoding per RFC 3986 — behind a codec object whose safe set is explicit and immutable. The trade-off: it does not split URIs or know which component it is encoding; the caller picks the safe set.

Encoding is defined over UTF-8 bytes, per RFC 3986 §2.5. The `plus_as_space` option is not part of RFC 3986; it exists because `application/x-www-form-urlencoded` is common enough to warrant a single opt-in flag rather than a separate library. It defaults to `False`.

## Edge cases

Decoding accepts lowercase hex digits, although encoding always emits uppercase. Truncated sequences (`%`, `%2`) and non-hex digits (`%GG`) raise `DecodingError`; invalid UTF-8 byte sequences from otherwise well-formed `%XX` pairs also raise `DecodingError`. Non-`str` inputs raise `EncodingError` or `DecodingError` rather than `TypeError`, so callers can catch all codec failures with a single except clause.
