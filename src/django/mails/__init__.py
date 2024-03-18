from django.conf import settings
import cfg.cfg as cfg


def apply_settings():
    settings.EMAIL_HOST = cfg.get_value("email_server", "")
    settings.EMAIL_PORT = cfg.get_value("email_port", 587)
    settings.EMAIL_HOST_USER = cfg.get_value("email_user", "")
    settings.EMAIL_HOST_PASSWORD = cfg.get_value("email_password", "")
    settings.EMAIL_USE_TLS = cfg.get_value("email_encryption", "TLS") == "TLS"
    settings.EMAIL_USE_SSL = cfg.get_value("email_encryption", "TLS") == "SSL"

apply_settings()