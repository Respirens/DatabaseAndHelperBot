import json
import os


class Config:

    DEFAULT_CONFIG = {
        "bot_token": "change_this_bot_token",
        "password": "change_this_password",
        "admin_password": "change_this_admin_password"
    }

    instance = None

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = Config(cls.DEFAULT_CONFIG)
        return cls.instance

    def __init__(self, default_config):
        if os.path.exists("config.json"):
            with open("config.json") as config_file:
                self.config = json.load(config_file)
        else:
            with open("config.json", "w") as config_file:
                json.dump(default_config, config_file, indent=2)
            print("Config file does not exist, default config will be created")
            print("Set the bot token and passwords in the config, then run the bot")
            self.config = default_config

    def get(self, key):
        return self.config.get(key)

    def set(self, key, value):
        self.config[key] = value

    def save(self):
        with open("config.json", "w") as config_file:
            json.dump(self.config, config_file, indent=2)

    def reload(self):
        with open("config.json") as config_file:
            self.config = json.load(config_file)
