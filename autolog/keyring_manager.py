"""Handles secure credential storage"""

import keyring


class CredentialManager:
    SERVICE_NAME = "jira_worklog_app"

    @classmethod
    def save_credentials(cls, base_url, email, api_key):
        keyring.set_password(cls.SERVICE_NAME, "base_url", base_url)
        keyring.set_password(cls.SERVICE_NAME, "email", email)
        keyring.set_password(cls.SERVICE_NAME, "api_key", api_key)

    @classmethod
    def get_credentials(cls):
        base_url = keyring.get_password(cls.SERVICE_NAME, "base_url")
        email = keyring.get_password(cls.SERVICE_NAME, "email")
        api_key = keyring.get_password(cls.SERVICE_NAME, "api_key")
        return base_url, email, api_key
