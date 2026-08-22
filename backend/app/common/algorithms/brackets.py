"""Stack-based bracket/quote balance check.

Used on LLM-generated SQL before it reaches Postgres: a dangling "(" or an
unterminated string literal is caught here with a precise message instead of
an opaque syntax error. Walk the text once; push openers, pop on closers and
require the types to match; the stack must be empty at the end. Quotes
toggle an "in string" state so brackets inside a literal are ignored.

O(n) time, O(depth) space. LeetCode analog: Valid Parentheses (#20).
"""

from __future__ import annotations

_PAIRS = {")": "(", "]": "[", "}": "{"}
_OPENERS = set(_PAIRS.values())


def check_balanced(text: str) -> str | None:
    """Returns None if balanced, else a human-readable problem description."""
    stack: list[tuple[str, int]] = []
    quote: str | None = None          # currently-open string delimiter
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch in _OPENERS:
            stack.append((ch, i))
        elif ch in _PAIRS:
            if not stack:
                return f"Unexpected '{ch}' at position {i}"
            opener, _ = stack.pop()
            if opener != _PAIRS[ch]:
                return f"Mismatched '{opener}' ... '{ch}' at position {i}"
    if quote:
        return f"Unterminated string literal ({quote})"
    if stack:
        opener, pos = stack[-1]
        return f"Unclosed '{opener}' opened at position {pos}"
    return None
