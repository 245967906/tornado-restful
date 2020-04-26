import json
import os
import re
from functools import reduce
from operator import getitem
from typing import Any

_default_locale = "en"
_translations = {}


def set_default_locale(locale: str) -> None:
    global _default_locale
    _default_locale = locale


def load_translations(path: str) -> None:
    global _translations
    for filename in os.listdir(path):
        if not re.match(r"[a-z]+(_[A-Z]+)?\.json$", filename):
            continue
        with open(os.path.join(path, filename)) as f:
            locale, _ = os.path.splitext(filename)
            _translations[locale] = json.loads(f.read())


class I18n:
    def __init__(self, code: str) -> None:
        self.code = code

    def get_closest(self) -> str:
        supported_locales = _translations.keys()
        code = self.code.replace("-", "_")
        parts = code.split("_")
        if len(parts) == 2:
            code = parts[0].lower() + "_" + parts[1].upper()
        if code in supported_locales:
            return code
        if parts[0].lower() in supported_locales:
            return parts[0].lower()
        return _default_locale

    def translate(self, placeholder: str, **kwargs: Any) -> str:
        snippets = placeholder.split(".")
        translations = _translations.get(self.get_closest())
        try:
            message = reduce(getitem, snippets, translations)
        except KeyError:
            message = placeholder
        return message if not kwargs else message.format(**kwargs)

    t = translate
