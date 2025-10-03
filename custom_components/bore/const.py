"""Constants for the Bore integration."""

DOMAIN = "bore"

CONF_LOCAL_PORT = "local_port"
CONF_LOCAL_HOST = "local_host"
CONF_TO = "to"
CONF_PORT = "port"
CONF_SECRET = "secret"
CONF_CHECK_URL = "check_url"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_LOCAL_HOST = "localhost"
DEFAULT_PORT = 0
DEFAULT_UPDATE_INTERVAL = "5 minutes"

UPDATE_INTERVALS = [
    "30 seconds",
    "1 minute",
    "2 minutes",
    "5 minutes",
    "15 minutes",
    "30 minutes",
    "60 minutes",
    "6 hours",
    "24 hours",
]
