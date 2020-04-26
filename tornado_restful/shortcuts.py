import importlib
import os
import re
from datetime import datetime, timedelta
from inspect import getmembers
from passlib.hash import pbkdf2_sha256
from types import ModuleType
from typing import List, Optional, Union

import jwt
import tornado.web

from tornado_restful.conf import settings
from tornado_restful.routers import Router
from tornado_restful.utils import SMTP, AESCipher


def _load_modules_from_spec_path(path: str) -> List[ModuleType]:
    pattern = r"^[a-zA-Z].*\.py"
    modules = []
    for filename in os.listdir(path):
        if not re.match(pattern, filename):
            continue
        root, _ = os.path.splitext(filename)
        package = os.path.relpath(path).replace(os.sep, ".")
        module = importlib.import_module(package + "." + root)
        modules.append(module)
    return modules


def get_routes(
    path: str = settings.routers_path,
    api_prefix: str = settings.api_prefix,
    trailing_slash: bool = settings.trailing_slash,
) -> List[tornado.web.url]:
    routes = []
    for module in _load_modules_from_spec_path(path):
        routers = [
            router for _, router in getmembers(module)
            if isinstance(router, Router)
        ]
        for router in routers:
            router.api_prefix = api_prefix
            router.trailing_slash = trailing_slash
            routes += router.rules
    return routes


def send_email(
    subject: str = "",
    message: str = "",
    to: Union[str, List[str]] = None,
    subtype: str = "plain",
) -> None:
    with SMTP(
        host=settings.email_host,
        port=settings.email_port,
        user=settings.email_user,
        password=settings.email_password,
        tls=settings.email_use_tls,
        timeout=settings.email_timeout,
    ) as smtp:
        smtp.content_subtype = subtype
        smtp.sendmail(subject, message, settings.email_user, to)


def generate_json_web_token(
    payload: dict,
    expires_in: int = settings.jwt_expiration_delta,
) -> str:
    payload["exp"] = datetime.utcnow() + timedelta(seconds=expires_in)
    token = jwt.encode(
        payload=payload,
        key=settings.secret_key,
        algorithm=settings.jwt_algorithms,
    ).decode("utf-8")
    return token


def parse_json_web_token(
    token: str,
    verify_exp: bool = True,
) -> Optional[dict]:
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.secret_key,
            algorithms=settings.jwt_algorithms,
            leeway=settings.jwt_leeway,
            options={"verify_exp": verify_exp},
        )
    except (
        jwt.DecodeError,
        jwt.ExpiredSignatureError,
        jwt.InvalidSignatureError,
    ):
        payload = None
    return payload


def encrypt(plaintext: str) -> str:
    cipher = AESCipher(settings.secret_key[:16])
    return cipher.encrypt(plaintext)


def decrypt(ciphertext: str) -> str:
    cipher = AESCipher(settings.secret_key[:16])
    return cipher.decrypt(ciphertext)


def verify_password(password, hashed):
    return pbkdf2_sha256.verify(password, hashed)
