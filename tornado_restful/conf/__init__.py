import importlib
import os

from tornado_restful.conf import global_settings

ENVIRONMENT_VARIABLE = "TORNADO_SETTINGS_MODULE"


class Settings:
    def __init__(self) -> None:
        settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
        if not settings_module:
            raise AssertionError(
                "Requested settings, but settings are not configured. "
                "You must define the environment variable %s before "
                "accessing settings." % ENVIRONMENT_VARIABLE
            )
        mod = importlib.import_module(settings_module)

        for setting in dir(global_settings):
            if not setting.startswith("_"):
                setattr(self, setting, getattr(global_settings, setting))
        for setting in dir(mod):
            if not setting.startswith("_"):
                setattr(self, setting, getattr(mod, setting))


settings = Settings()
