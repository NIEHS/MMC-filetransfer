from pydantic import BaseSettings
from pathlib import Path
from uuid import UUID

project_path = Path(__file__).absolute().parents[2] 
config_path = project_path / 'config'

class Settings(BaseSettings):
    bbcp: Path
    IMOD_BIN: Path
    scipion_path: Path
    
    # group: str
    HTML: Path
    scipion_loc: Path
    logs: Path

    #STMP
    sender_email: str
    smtp_server: str
    smtp_port: int

    template_files: Path = project_path / 'Template_files'

    class Config:
        env_file = config_path / '.env'
        env_file_encoding = 'utf-8'
