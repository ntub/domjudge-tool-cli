import secrets
import string


def gen_password(
    length: int | None = None,
    pattern: str | None = None,
) -> str:
    pwd_length = length or 10
    pwd_pattern = pattern or (string.ascii_letters + string.digits)
    return "".join(secrets.choice(pwd_pattern) for _ in range(pwd_length))
