import math
from random import random
from http import cookies


def random_user_id():
    return pow(10, 15) + int(math.floor(2 * pow(10, 15) * random()))


def build_cookie_with_str(cookie_str):
    simple_cookie = cookies.SimpleCookie(cookie_str)  # Parse Cookie from str
    cookie = {key: morsel.value for key, morsel in simple_cookie.items()}
    return cookie
