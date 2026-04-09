import logging
import logging.config
import yaml
from MMC.cli.cli import load_commands
from MMC.lib.config import project_path, config_path, Settings
from MMC.lib.groups import load_groups, load_affiliations
from MMC.lib.storage import load_storageLocations
import sys


# Commands are loaded eagerly — they only require cli.yaml, not .env
commands = load_commands(project_path / 'MMC' / 'cli' / 'cli.yaml')

# Everything below requires a configured .env file
try:
    env = Settings()
except Exception as e:
    env = None
    _settings_error = e
else:
    _settings_error = None

def _require_env():
    if env is None:
        raise RuntimeError(
            f"MMC is not configured. Please create config/.env from the template.\n"
            f"Original error: {_settings_error}"
        ) from _settings_error

if env is not None:
    LOG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'generic': {
                'format': '%(asctime)s [%(name)s:%(lineno)s - %(levelname)8s]   %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'generic',
                'stream': sys.stdout,
            },
        },
        'loggers': {
            'root': {
                'level': env.log_level,
                'handlers': ['console'],
            },
        }
    }

    if env.logs is not None:
        LOG['handlers']['file'] = {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'generic',
            'filename': str(env.logs / 'mmc.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 14,
            'encoding': 'utf-8',
        }
        LOG['loggers']['root']['handlers'].append('file')

    logging.config.dictConfig(LOG)

    groups_file = config_path / 'groups.yaml'
    groups = load_groups(groups_file)
    affiliations = load_affiliations(config_path / 'affiliations.yaml')
    storageLocations = load_storageLocations(config_path / 'storageLocations.yaml')
else:
    groups = {}
    affiliations = []
    storageLocations = {}

email_contactList = config_path / 'contact_emails.txt'
interface = None

def _load_scopes(scopes_file):
    if not scopes_file.exists():
        return {}
    with open(scopes_file) as f:
        return yaml.safe_load(f) or {}

scopes = _load_scopes(config_path / 'scopes.yaml')
