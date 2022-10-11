from copy import copy
import datetime
import shutil
import time
from MMC.lib.email import send_email
from MMC.lib.groups import Group, GroupDoesNotExistError, ProjectDoesNotExistError
from MMC.lib.transfer import Movie, Transfer, remove_from_source, update_source
from pathlib import Path
from pydantic import BaseModel, validator, Field
from MMC import settings
import yaml
import traceback
import subprocess as sub
import shlex
import os


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
    print(f'Created settings file for session {session.session} at {file}')

def initiate_session(session: Session):
    session= Session.parse_obj({k:v for k,v in session.items() if v is not None})
    save_session(session)

def load_session_from_file(session:str):
    file = settings.env.logs / session / 'settings.yaml'
    if not file.is_file():
        print(f'No file found at {file}. Perhaps the session does not exist.')
        return
    yaml_file = yaml.safe_load(file.read_text())
    session = Session.parse_obj(yaml_file)
    return file, session


async def run_transfer(session:str, duration:float=16, cluster:bool=False):
    nochange = 0
    nochange_sleep = 120
    idle_time_notification = 2
    pool = 5
    restart = True
    duration_in_seconds = duration*60*60
    email_send_timeout = 90
    init_email_sent_time = time.time() - 90*60
    email_sent_time = copy(init_email_sent_time)
   

    start_time = time.time()
    file, session = load_session_from_file(session)
    # Adding start time to session file
    if session.status == 'created':
        session.set_startTime()
    session.status = 'started'
    save_session(session)
    transfer_obj = Transfer(session.sourceDir, delete=True, logdir=file.parent, filesPattern=session.filesPattern, gainReference=session.gainReference)

    print('Initiating transfer')
    try:
        transfer_locations = [settings.storageLocations['staging'], settings.storageLocations['longTerm']]
        if cluster:
            transfer_locations.append(settings.storageLocations['cluster'])
        
        for location in transfer_locations:
            location.set_session_path(session.specific_path)
            location.mkdir() 
        
        while not transfer_obj.gain_done:
            print('Looking for gain reference.')
            gainfiles = []
            for pattern in transfer_obj.gainReference:
                if Path(pattern).is_absolute:
                    pattern = Path(pattern)
                    if pattern.exists():
                        gainfiles += [pattern]
                        break
                gainfiles += session.source.glob(pattern)
            if gainfiles:
                gainfiles.sort(key= lambda x: x.stat().st_ctime)
                transfer_obj.process_gain(gainfiles[0], transfer_locations[0].session_raw_path)
                break
            print(f'Gain reference with patterns {transfer_obj.gainReference} not found, waiting 2 min.')
            time.sleep(120)
        session.status = 'transferring'
        save_session(session)
        while True:
            idle_time = nochange*nochange_sleep/60
            print(f'No files were found in the last {idle_time:.1f} minutes.')
            if idle_time >= idle_time_notification and time.time() - email_sent_time >= email_send_timeout*60:
                email_sent_time = time.time()
                print(f'Sending email.')
                send_email(
                    title= f'WARNING: {session.session} No files found in {idle_time:.0f} mintues', 
                    message= f'Something may be wrong with data collection.\nSession information:\n\n{file.read_text()}',
                    #contacts= session.project_obj.emailList
                    )
            if time.time() - start_time >= duration_in_seconds:
                print(f'Time limit of {duration}h has been reached')
                break

            new_files = transfer_obj.list_source()
            if not new_files and not restart: 
                nochange += 1
                print(f'Will look for files again in {nochange_sleep/60:.1f} min')
                time.sleep(nochange_sleep)
                continue

            nochange = 0
            email_sent_time = copy(init_email_sent_time)
            final_status = [location.status for location in transfer_locations]
            while True:
                restart = False
                if not transfer_obj.get_subset(final_status,pool=pool):
                    break
                for location in transfer_locations:
                    print(f'Moving files to {location.status} {location.session_raw_path}.')
                    to_transfer = transfer_obj.get_subset([location.status],pool=pool)
                    if len(to_transfer) == 0:
                        continue
                    results = await location.transfer(to_transfer,location.session_raw_path)
                    if transfer_obj.delete and location.status =='staging':
                        results = remove_from_source(results,delete_status=[location.status])
                    if location.status == 'staging':
                        results = update_source(results,location.session_raw_path)
                    transfer_obj.tansfer_list = set(transfer_obj.transfer_list).update(results)
                    transfer_obj.save()
                    # print(results)
        session.status = 'completed'
    except KeyboardInterrupt:
        print('Interrupting')
        session.status = 'killed'
    except Exception as err:
        print(traceback.format_exc())
        session.status = 'error'
        send_email(
            title= f'ERROR: {session.session}', 
            message= f'The file transfer has terminated unexpectedly.\nSession information:\n\n{file.read_text()}\n\nTraceback:\n{traceback.format_exc()}',
            #contacts= session.project_obj.emailList
            )
    finally:
        print('Saving and exiting.')
        session.set_endTime()
        session.set_duration()
        session.numberOfMovies = len([f for f in transfer_obj.transfer_list if not '.mdoc' in f.path.name and not 'gain' in f.path.name]) - 1
        save_session(session)
        transfer_obj.save()
        if session.status == 'completed':
            send_email(
                title= f'COMPLETED: {session.session} is finished.', 
                message= f'Session information:\n\n{file.read_text()}',
                contacts= session.project_obj.emailList
                )
        for location in transfer_locations:
            await location.transfer([Movie(file, delete=False),Movie(transfer_obj.logfile,delete=False)],location.session_path)

def preprocess(session: str, scipion:bool=True, timeout:float=16):
    from MMC.lib.scipion_workflow import scipion_template
    file, session = load_session_from_file(session)

    if scipion:
        print('Creating scipion workflow')
        html_destination = settings.env.HTML / session.group / 'reports'
        phpFile = html_destination.parent / 'index.php'
        phpFile.parent.mkdir(exist_ok=True, parents=True)
        if not phpFile.exists():
            shutil.copy(Path(settings.env.template_files,'index.php'), phpFile)
        raw_path = settings.storageLocations['staging'].set_session_path(session.specific_path) / 'raw'
        workflow = scipion_template()
        workflow.set_values([
                ('import', 'filesPath', str(raw_path)),
                ('import', 'timeout', 240*60),
                ('import', 'gainFile', str(raw_path / 'gain.mrc') if not 'epu' in session.scope else str(raw_path / 'gain.tiff')),
                ('monitor', 'monitorTime', int(timeout * 60)),
                ('monitor', 'publishCmd', f'rsync -avL %(REPORT_FOLDER)s {html_destination}'),
                ('import', 'dosePerFrame', session.totalDose/ session.frameNumber),
                ('import', 'samplingRate', session.pixelSize),
                ('import', 'magnification', session.magnification),
            ])
        workflow.set_scope_defaults(session.scope)
        if not workflow.check_completion():
            return 
        wf = workflow.save_template(file.parent/'scipion_workflow.json')
        scipion_session_directory = settings.env.scipion_loc/session.specific_path
        scipion_session_directory.mkdir(parents=True,exist_ok=True)
        print('All arguments for scipion processing present.\nCreating Scipion project. Scheduling will occur after the gain is transfered.')
        command = f"""{str(settings.env.scipion_path)} python -m pyworkflow.project.scripts.create "{session.session}" "{wf}" "{str(scipion_session_directory)}" """
        print(command)
        p = sub.run(shlex.split(command),stdout=sub.DEVNULL, stderr=sub.DEVNULL)
        time.sleep(5)
        while True:
            _, session = load_session_from_file(session.session)
            if len(list(raw_path.glob('gain*'))) > 0:
                print('Found gain in import directory. Starting Scipion.')
                command = f"{str(settings.env.scipion_path)} python -m pyworkflow.project.scripts.schedule {session.session}"
                print(command)
                p = sub.Popen(shlex.split(command),stdout=sub.DEVNULL, stderr=sub.DEVNULL, preexec_fn=os.setpgrp)   
                return
            print('Waiting for gain file to be transfered.')
            time.sleep(120)             