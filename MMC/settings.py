import logging
import logging.config
from MMC.cli.cli import load_commands
from MMC.lib.config import project_path, config_path, Settings
from MMC.lib.groups import load_groups
from MMC.lib.storage import load_storageLocations
import sys


env = Settings()

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
            'handlers': ['console', ],
        },
    }
}

if env.logs is not None:
    LOG['handlers']['file'] = {
        'class': 'logging.handlers.TimedRotatingFileHandler',
        'formatter': 'generic',
        'filename': str(env.logs / 'logs' /'mmc.log'),
        'when': 'midnight',
        'interval': 1,
        'backupCount': 14,
        'encoding': 'utf-8',
    }
    LOG['loggers']['root']['handlers'].append('file')

logging.config.dictConfig(LOG)


groups_file = config_path / 'groups.yaml'
groups = load_groups(groups_file)
commands = load_commands(project_path / 'MMC'/ 'cli' / 'cli.yaml')
storageLocations= load_storageLocations(config_path/ 'storageLocations.yaml')
email_contactList = config_path / 'contact_emails.txt'

interface = None


niehs_arctica = {
    "voltage": 200,
    "sphericalAberration": 2.7,
    "amplitudeContrast": 0.1,
    "gainRot": 3,
    "gainFlip": 2,
    "filesPattern": "*.tif",
    "gpuList": "0 1"
}

niehs_Krios_EPU = {
    "voltage": 300,
    "sphericalAberration": 2.7,
    "amplitudeContrast": 0.1,
    "gainRot": 0,
    "gainFlip": 0,
    "filesPattern": "*_fractions.tiff",
    "gpuList": "2 3"
}

niehs_Krios = {
    "voltage": 300,
    "sphericalAberration": 2.7,
    "amplitudeContrast": 0.1,
    "gainRot": 0,
    "gainFlip": 0,
    "filesPattern": "*.tif",
    "gpuList": "2 3"
}

scopes = {'niehs_arctica': niehs_arctica, 'niehs_krios_epu': niehs_Krios_EPU, 'niehs_krios': niehs_Krios}
