from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List

project_path = Path(__file__).absolute().parents[2]
config_path = project_path / 'config'

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=config_path / '.env',
        env_file_encoding='utf-8',
    )

    bbcp: Path
    IMOD_BIN: Path
    scipion_path: Path

    HTML: Path
    logs: Path
    log_level: str

    #STMP
    smtp_username: str
    smtp_server: str
    smtp_port: int

    # REST API
    cors_origins: List[str] = []


    template_files: Path = project_path / 'Template_files'

    @property
    def sessionsDirectory(self):
        return self.logs / 'sessions'
