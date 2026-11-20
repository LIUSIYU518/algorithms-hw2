CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encode(n):
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be a non-negative integer")
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    if n == 0:
        return "0"

    digits = []
    while n > 0:
        n, remainder = divmod(n, 62)
        digits.append(CHARS[remainder])
    return "".join(reversed(digits))

def decode(s):
    if not isinstance(s, str):
        raise TypeError("s must be a string")
    if not s:
        raise ValueError("s must not be empty")

    result = 0
    for char in s:
        try:
            digit = CHARS.index(char)
        except ValueError:
            raise ValueError(f"invalid base62 character: {char!r}") from None
        result = result * 62 + digit
    return result
