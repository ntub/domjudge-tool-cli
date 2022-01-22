import random
import string


def gen_password(length=None, pattern=None) -> str:
    if not length:
        length = 10

    if not pattern:
        pattern = string.ascii_letters + string.digits

    return "".join(random.choices(pattern, k=length))
