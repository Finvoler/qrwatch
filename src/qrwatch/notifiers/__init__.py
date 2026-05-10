"""Notifier interfaces and skeleton providers."""

from qrwatch.config import AppConfig
from qrwatch.config import ConfigError
from qrwatch.notifiers.base import DryRunNotifier, NotificationResult, Notifier
from qrwatch.notifiers.email import EmailNotifier

__all__ = [
    "DryRunNotifier",
    "EmailNotifier",
    "NotificationResult",
    "Notifier",
    "create_notifier",
]


EMAIL_PROVIDER_NAMES = {"email", "qq-mail", "qqmail"}


def create_notifier(config: AppConfig) -> Notifier:
    """Create the configured notifier.

    Dry-run mode always returns a dry-run notifier, even when the selected
    provider name is a future real provider.
    """

    provider = config.notifier_provider.strip().lower()
    if config.dry_run or provider == "dry-run":
        return DryRunNotifier(provider_name=config.notifier_provider)
    if provider in EMAIL_PROVIDER_NAMES:
        if config.smtp_username is None:
            raise ConfigError("SMTP username is required for email notifications")
        if config.smtp_password is None:
            raise ConfigError("SMTP password is required for email notifications")
        if config.notify_to is None:
            raise ConfigError("notification recipient is required for email notifications")
        return EmailNotifier(
            provider_name=config.notifier_provider,
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            smtp_username=config.smtp_username,
            smtp_password=config.smtp_password,
            smtp_use_ssl=config.smtp_use_ssl,
            smtp_timeout_seconds=config.smtp_timeout_seconds,
            notify_from=config.notify_from,
            notify_to=config.notify_to,
        )
    raise ConfigError(f"unsupported live notifier provider: {config.notifier_provider}")
