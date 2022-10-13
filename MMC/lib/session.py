import datetime
import time
from MMC.lib.groups import GroupDoesNotExistError, ProjectDoesNotExistError
from pathlib import Path
from pydantic import BaseModel, validator, Field
from MMC import settings
import yaml
import logging

logger = logging.getLogger(__name__)
affiliation_dir = {
    'NIEHS': '',
    'NICE': 'NICE',
    'Collaborations': 'BorgniaM/Collaborations/'
}

dateformat = "%Y-%m-%d %H:%M"

def string_to_timestamp(datetime_string:str):
    return time.mktime(datetime.datetime.strptime(datetime_string, dateformat).timetuple())

class Session(BaseModel):

    sourceDir: str = Field(alias="source", )
    group: str
    project: str
    sample: str 
   
    scope: str
    magnification: float
    pixelSize: float
    totalDose: float
    frameNumber: int
    detectorCounts: float

    mode: str = 'spr'
    tiltAngleOrScheme: str = '0'
    filesPattern: str | None = None
    gainReference: str | None = None
    date: str = datetime.date.today().strftime("%Y%m%d")

    status: str = 'created'
    startTime: str|None = None 
    endTime: str|None = None 
    durationInHours: float|None = None
    numberOfMovies: int|None = None

    class Config:
        allow_population_by_field_name = True

    @property
    def specific_path(self):
        return Path(affiliation_dir[settings.groups[self.group].affiliation], self.group, self.project , self.session)
    
    def set_startTime(self):
        self.startTime = datetime.datetime.now().strftime(dateformat)
    
    def set_endTime(self):
        self.endTime = datetime.datetime.now().strftime(dateformat)
    
    @property
    def startTimestamp(self):
        if self.startTime is not None:
            return string_to_timestamp(self.startTime)
    
    @property
    def endTimestamp(self):
        if self.endTime is not None:
            return string_to_timestamp(self.endTime)
    
    def set_duration(self):
        self.durationInHours = round((self.endTimestamp - self.startTimestamp) /60 /60,1)
    
    @property
    def group_obj(self):
        return settings.groups[self.group]
    
    @property
    def project_obj(self):
        return next((item for item in  settings.groups[self.group].projects if item.name == self.project), None)

    @property
    def longTermDir(self):
        return settings.env.ddn_root / settings.env.ddn_raw_dir / self.specific_path

    @property
    def stagingDir(self):
        return settings.env.local_dir / self.specific_path
    
    @property
    def session(self):
        return '_'.join([self.date,self.sample])
    
    @property
    def source(self):
        return Path(self.sourceDir)

    @property
    def gainReferencePatterns(self):
        if self.gainReference is None:
            return ['*Ref*', '*Gain*', '*gain*', '*/*/Data/*_gain.tiff']
        return [self.gainReference]

    @validator('group', pre=True)
    def is_group_exists(cls,v):
        if v in settings.groups:
            return v
        else:
            raise GroupDoesNotExistError()
    
    @validator('project')
    def is_project_exists(cls,v, values):
        if v in list(map(lambda x: x.name, settings.groups[values['group']].projects)):
            return v
        raise ProjectDoesNotExistError()

def save_session(session:Session, directory:Path = settings.env.logs):
    path = directory / session.session
    path.mkdir(exist_ok=True)
    file = path / 'settings.yaml'
    with open(file, 'w') as f:
        f.write(yaml.dump(session.dict()))
    logger.info(f'Created settings file for session {session.session} at {file}')

def initiate_session(session: Session):
    session= Session.parse_obj({k:v for k,v in session.items() if v is not None})
    save_session(session)

def load_session_from_file(session:str):
    file = settings.env.logs / session / 'settings.yaml'
    if not file.is_file():
        logger.info(f'No file found at {file}. Perhaps the session does not exist.')
        return
    yaml_file = yaml.safe_load(file.read_text())
    session = Session.parse_obj(yaml_file)
    return file, session