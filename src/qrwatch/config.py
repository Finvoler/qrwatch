"""Configuration loading for QR Watch."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values


DEFAULT_INTERVAL_SECONDS = 30.0
DEFAULT_NOTIFIER_PROVIDER = "dry-run"
DEFAULT_CREDENTIAL_SOURCES = ("env",)
DEFAULT_DEDUP_WINDOW_SECONDS = 300.0
DEFAULT_SMTP_HOST = "smtp.qq.com"
DEFAULT_SMTP_PORT = 465
DEFAULT_SMTP_TIMEOUT_SECONDS = 10.0
DEFAULT_MONITOR_INDEX = 1
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_SAVE_SCREENSHOTS = False
DEFAULT_SCREENSHOT_MAX_COUNT = 200
DEFAULT_SCREENSHOT_MAX_AGE_DAYS = 1.0
DEFAULT_CONFIG_FILENAME = "config.env"

ENV_CONFIG_FILE = "QRWATCH_CONFIG_FILE"
ENV_INTERVAL_SECONDS = "QRWATCH_INTERVAL_SECONDS"
ENV_NOTIFIER_PROVIDER = "QRWATCH_NOTIFY_PROVIDER"
ENV_DRY_RUN = "QRWATCH_DRY_RUN"
ENV_CREDENTIAL_SOURCES = "QRWATCH_CREDENTIAL_SOURCES"
ENV_DEDUP_WINDOW_SECONDS = "QRWATCH_DEDUP_WINDOW_SECONDS"
ENV_STATE_PATH = "QRWATCH_STATE_PATH"
ENV_LOG_DIR = "QRWATCH_LOG_DIR"
ENV_SCREENSHOT_DIR = "QRWATCH_SCREENSHOT_DIR"
ENV_SAVE_SCREENSHOTS = "QRWATCH_SAVE_SCREENSHOTS"
ENV_SCREENSHOT_MAX_COUNT = "QRWATCH_SCREENSHOT_MAX_COUNT"
ENV_SCREENSHOT_MAX_AGE_DAYS = "QRWATCH_SCREENSHOT_MAX_AGE_DAYS"
ENV_LOG_LEVEL = "QRWATCH_LOG_LEVEL"
ENV_MONITOR_INDEX = "QRWATCH_MONITOR_INDEX"
ENV_SMTP_HOST = "QRWATCH_SMTP_HOST"
ENV_SMTP_PORT = "QRWATCH_SMTP_PORT"
ENV_SMTP_USERNAME = "QRWATCH_SMTP_USERNAME"
ENV_SMTP_PASSWORD = "QRWATCH_SMTP_PASSWORD"
ENV_SMTP_USE_SSL = "QRWATCH_SMTP_USE_SSL"
ENV_SMTP_TIMEOUT_SECONDS = "QRWATCH_SMTP_TIMEOUT_SECONDS"
ENV_NOTIFY_FROM = "QRWATCH_NOTIFY_FROM"
ENV_NOTIFY_TO = "QRWATCH_NOTIFY_TO"

STARTER_CONFIG_CONTENT = """QRWATCH_INTERVAL_SECONDS=30
QRWATCH_MONITOR_INDEX=1
QRWATCH_NOTIFY_PROVIDER=dry-run
QRWATCH_DRY_RUN=true
QRWATCH_CREDENTIAL_SOURCES=env
QRWATCH_DEDUP_WINDOW_SECONDS=300
QRWATCH_LOG_LEVEL=INFO
QRWATCH_SAVE_SCREENSHOTS=false
QRWATCH_SCREENSHOT_MAX_COUNT=200
QRWATCH_SCREENSHOT_MAX_AGE_DAYS=1

# Runtime files default to %LOCALAPPDATA%\\QRWatch.
# Uncomment these only if you need custom locations.
# QRWATCH_STATE_PATH=C:\\Users\\you\\AppData\\Local\\QRWatch\\dedup-state.json
# QRWATCH_LOG_DIR=C:\\Users\\you\\AppData\\Local\\QRWatch\\logs
# QRWATCH_SCREENSHOT_DIR=C:\\Users\\you\\AppData\\Local\\QRWatch\\screenshots

# QQ Mail-compatible SMTP settings for live email sends.
# Keep QRWATCH_DRY_RUN=true until credentials are supplied and verified.
# QRWATCH_NOTIFY_PROVIDER=qq-mail
# QRWATCH_DRY_RUN=false
# QRWATCH_SMTP_HOST=smtp.qq.com
# QRWATCH_SMTP_PORT=465
# QRWATCH_SMTP_USERNAME=your-address@qq.com
# QRWATCH_SMTP_PASSWORD=your-local-authorization-code
# QRWATCH_NOTIFY_TO=receiver@example.com
"""


class ConfigError(ValueError):
    """Raised when QR Watch configuration is invalid."""


@dataclass(frozen=True)
class AppConfig:
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS
    notifier_provider: str = DEFAULT_NOTIFIER_PROVIDER
    dry_run: bool = True
    credential_sources: tuple[str, ...] = DEFAULT_CREDENTIAL_SOURCES
    config_path: Path | None = None
    dedup_window_seconds: float = DEFAULT_DEDUP_WINDOW_SECONDS
    state_path: Path = field(default_factory=lambda: default_state_path(os.environ))
    log_dir: Path = field(default_factory=lambda: default_log_dir(os.environ))
    screenshot_dir: Path = field(
        default_factory=lambda: default_screenshot_dir(os.environ)
    )
    save_screenshots: bool = DEFAULT_SAVE_SCREENSHOTS
    screenshot_max_count: int = DEFAULT_SCREENSHOT_MAX_COUNT
    screenshot_max_age_days: float = DEFAULT_SCREENSHOT_MAX_AGE_DAYS
    log_level: str = DEFAULT_LOG_LEVEL
    monitor_index: int = DEFAULT_MONITOR_INDEX
    smtp_host: str = DEFAULT_SMTP_HOST
    smtp_port: int = DEFAULT_SMTP_PORT
    smtp_username: str | None = field(default=None, repr=False)
    smtp_password: str | None = field(default=None, repr=False)
    smtp_use_ssl: bool = True
    smtp_timeout_seconds: float = DEFAULT_SMTP_TIMEOUT_SECONDS
    notify_from: str | None = None
    notify_to: str | None = None

    def validated(self) -> "AppConfig":
        if self.interval_seconds <= 0:
            raise ConfigError("interval must be greater than zero seconds")
        provider = self.notifier_provider.strip().lower()
        if not provider:
            raise ConfigError("notifier provider must not be empty")
        if not self.credential_sources:
            raise ConfigError("at least one credential source is required")
        if any(not source.strip() for source in self.credential_sources):
            raise ConfigError("credential sources must not contain empty values")
        if self.dedup_window_seconds <= 0:
            raise ConfigError("deduplication window must be greater than zero seconds")
        if self.monitor_index < 0:
            raise ConfigError("monitor index must be zero or greater")
        if self.log_level.strip().upper() not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            raise ConfigError("log level must be DEBUG, INFO, WARNING, or ERROR")
        if self.screenshot_max_count <= 0:
            raise ConfigError("screenshot max count must be greater than zero")
        if self.screenshot_max_age_days <= 0:
            raise ConfigError("screenshot max age must be greater than zero days")
        if self.smtp_port <= 0:
            raise ConfigError("SMTP port must be greater than zero")
        if not self.smtp_host.strip():
            raise ConfigError("SMTP host must not be empty")
        if self.smtp_timeout_seconds <= 0:
            raise ConfigError("SMTP timeout must be greater than zero seconds")
        if not self.dry_run:
            if provider == "dry-run":
                raise ConfigError("real notifier provider is required when dry-run is disabled")
            if provider in {"email", "qq-mail", "qqmail"}:
                if not self.smtp_username:
                    raise ConfigError("SMTP username is required for email notifications")
                if not self.smtp_password:
                    raise ConfigError("SMTP password is required for email notifications")
                if not self.notify_to:
                    raise ConfigError("notification recipient is required for email notifications")
        return self


def load_config(
    *,
    env: Mapping[str, str] | None = None,
    config_path: str | Path | None = None,
    use_default_config_file: bool = False,
    create_default_config: bool = False,
) -> AppConfig:
    """Load configuration from an optional dotenv file and environment variables.

    Values from environment variables override values from the config file.
    Secrets may be read for real notifiers, but they must never be logged or
    committed.
    """

    current_env = os.environ if env is None else env
    selected_path = _resolve_config_path(
        config_path,
        current_env,
        use_default_config_file=use_default_config_file,
    )
    explicit_config_path = config_path is not None or bool(current_env.get(ENV_CONFIG_FILE))
    values: dict[str, str] = {}

    if selected_path is not None:
        if not selected_path.exists():
            if create_default_config and not explicit_config_path:
                write_starter_config(selected_path)
            else:
                raise ConfigError(f"config file does not exist: {selected_path}")
        values.update(
            {
                key: value
                for key, value in dotenv_values(selected_path).items()
                if value is not None
            }
        )

    values.update(
        {
            key: current_env[key]
            for key in (
                ENV_INTERVAL_SECONDS,
                ENV_NOTIFIER_PROVIDER,
                ENV_DRY_RUN,
                ENV_CREDENTIAL_SOURCES,
                ENV_DEDUP_WINDOW_SECONDS,
                ENV_STATE_PATH,
                ENV_LOG_DIR,
                ENV_SCREENSHOT_DIR,
                ENV_SAVE_SCREENSHOTS,
                ENV_SCREENSHOT_MAX_COUNT,
                ENV_SCREENSHOT_MAX_AGE_DAYS,
                ENV_LOG_LEVEL,
                ENV_MONITOR_INDEX,
                ENV_SMTP_HOST,
                ENV_SMTP_PORT,
                ENV_SMTP_USERNAME,
                ENV_SMTP_PASSWORD,
                ENV_SMTP_USE_SSL,
                ENV_SMTP_TIMEOUT_SECONDS,
                ENV_NOTIFY_FROM,
                ENV_NOTIFY_TO,
            )
            if key in current_env
        }
    )

    return AppConfig(
        interval_seconds=parse_interval(
            values.get(ENV_INTERVAL_SECONDS, str(DEFAULT_INTERVAL_SECONDS))
        ),
        notifier_provider=values.get(
            ENV_NOTIFIER_PROVIDER, DEFAULT_NOTIFIER_PROVIDER
        ).strip(),
        dry_run=parse_bool(values.get(ENV_DRY_RUN, "true")),
        credential_sources=parse_credential_sources(
            values.get(ENV_CREDENTIAL_SOURCES, ",".join(DEFAULT_CREDENTIAL_SOURCES))
        ),
        config_path=selected_path,
        dedup_window_seconds=parse_dedup_window(
            values.get(ENV_DEDUP_WINDOW_SECONDS, str(DEFAULT_DEDUP_WINDOW_SECONDS))
        ),
        state_path=Path(
            values.get(ENV_STATE_PATH)
            or str(default_state_path(current_env))
        ),
        log_dir=Path(values.get(ENV_LOG_DIR) or str(default_log_dir(current_env))),
        screenshot_dir=Path(
            values.get(ENV_SCREENSHOT_DIR) or str(default_screenshot_dir(current_env))
        ),
        save_screenshots=parse_bool(
            values.get(ENV_SAVE_SCREENSHOTS, str(DEFAULT_SAVE_SCREENSHOTS))
        ),
        screenshot_max_count=parse_positive_int(
            values.get(ENV_SCREENSHOT_MAX_COUNT, str(DEFAULT_SCREENSHOT_MAX_COUNT)),
            name="screenshot max count",
        ),
        screenshot_max_age_days=parse_positive_float(
            values.get(
                ENV_SCREENSHOT_MAX_AGE_DAYS,
                str(DEFAULT_SCREENSHOT_MAX_AGE_DAYS),
            ),
            name="screenshot max age",
        ),
        log_level=values.get(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL).strip().upper(),
        monitor_index=parse_non_negative_int(
            values.get(ENV_MONITOR_INDEX, str(DEFAULT_MONITOR_INDEX)),
            name="monitor index",
        ),
        smtp_host=values.get(ENV_SMTP_HOST, DEFAULT_SMTP_HOST).strip(),
        smtp_port=parse_positive_int(
            values.get(ENV_SMTP_PORT, str(DEFAULT_SMTP_PORT)),
            name="SMTP port",
        ),
        smtp_username=optional_str(values.get(ENV_SMTP_USERNAME)),
        smtp_password=optional_str(values.get(ENV_SMTP_PASSWORD)),
        smtp_use_ssl=parse_bool(values.get(ENV_SMTP_USE_SSL, "true")),
        smtp_timeout_seconds=parse_positive_float(
            values.get(ENV_SMTP_TIMEOUT_SECONDS, str(DEFAULT_SMTP_TIMEOUT_SECONDS)),
            name="SMTP timeout",
        ),
        notify_from=optional_str(values.get(ENV_NOTIFY_FROM)),
        notify_to=optional_str(values.get(ENV_NOTIFY_TO)),
    ).validated()


def parse_interval(value: str) -> float:
    try:
        interval = float(value)
    except ValueError as exc:
        raise ConfigError("interval must be a number of seconds") from exc
    if interval <= 0:
        raise ConfigError("interval must be greater than zero seconds")
    return interval


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ConfigError(f"invalid boolean value: {value}")


def parse_credential_sources(value: str) -> tuple[str, ...]:
    sources = tuple(part.strip() for part in value.split(",") if part.strip())
    if not sources:
        raise ConfigError("at least one credential source is required")
    return sources


def parse_dedup_window(value: str) -> float:
    try:
        window = float(value)
    except ValueError as exc:
        raise ConfigError("deduplication window must be a number of seconds") from exc
    if window <= 0:
        raise ConfigError("deduplication window must be greater than zero seconds")
    return window


def parse_positive_int(value: str, *, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ConfigError(f"{name} must be greater than zero")
    return parsed


def parse_non_negative_int(value: str, *, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if parsed < 0:
        raise ConfigError(f"{name} must be zero or greater")
    return parsed


def parse_positive_float(value: str, *, name: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number of seconds") from exc
    if parsed <= 0:
        raise ConfigError(f"{name} must be greater than zero seconds")
    return parsed


def optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def default_state_path(env: Mapping[str, str] | None = None) -> Path:
    return default_runtime_dir(env) / "dedup-state.json"


def default_log_dir(env: Mapping[str, str] | None = None) -> Path:
    return default_runtime_dir(env) / "logs"


def default_screenshot_dir(env: Mapping[str, str] | None = None) -> Path:
    return default_runtime_dir(env) / "screenshots"


def default_config_path(env: Mapping[str, str] | None = None) -> Path:
    return default_runtime_dir(env) / DEFAULT_CONFIG_FILENAME


def default_runtime_dir(env: Mapping[str, str] | None = None) -> Path:
    current_env = os.environ if env is None else env
    if current_env.get("LOCALAPPDATA"):
        return Path(current_env["LOCALAPPDATA"]) / "QRWatch"
    return Path.home() / "AppData" / "Local" / "QRWatch"


def write_starter_config(path: str | Path) -> Path:
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config_path.write_text(STARTER_CONFIG_CONTENT, encoding="utf-8")
    return config_path


def _resolve_config_path(
    config_path: str | Path | None,
    env: Mapping[str, str],
    *,
    use_default_config_file: bool = False,
) -> Path | None:
    if config_path is not None:
        return Path(config_path)
    if env.get(ENV_CONFIG_FILE):
        return Path(env[ENV_CONFIG_FILE])
    if use_default_config_file:
        return default_config_path(env)
    return None
