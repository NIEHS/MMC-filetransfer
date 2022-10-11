from MMC.cli.cli import load_commands
from MMC.lib.config import project_path, config_path, Settings
from MMC.lib.groups import load_groups
from MMC.lib.storage import load_storageLocations

env = Settings()

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
    # "magnification": 45000,
    # "samplingRate": 0.932,
    # "dosePerFrame": 0.8,
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