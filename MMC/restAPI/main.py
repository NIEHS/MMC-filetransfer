from pathlib import Path
from typing import List
from fastapi import FastAPI, status, Response, BackgroundTasks
from MMC.lib.groups import Group, save_groups
from MMC.lib.session import Session, load_session_from_file, save_session, find_session_directory, filter_sessions
from MMC import settings
import logging

from MMC.preprocess.session import preprocess, run_transfer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://mri20-dtn01:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

@app.get('/groups/list/')
async def display_group_info():
    return settings.groups

@app.post('/groups/add', status_code=status.HTTP_201_CREATED, )
async def add_group(group:Group,response:Response):
    if group.name in settings.groups:
        logger.info(f'Group {group.name} already exists')
        response.status_code = status.HTTP_208_ALREADY_REPORTED
        return settings.groups[group.name]
    settings.groups[group.name] = group
    save_groups(settings.groups, settings.groups_file)
    return settings.groups

@app.patch('/groups/update')
async def update_group(group:Group,response:Response):
    settings.groups[group.name] = group
    groups = save_groups(settings.groups, settings.groups_file)
    logger.info(f'Updated group {group}')
    logger.info(f'{groups}')
    return groups

@app.get('/sessions/find/')
async def find_sessions(group:str='*',project:str='*',session:str='*'):
    sessions = filter_sessions(group,project,session)
    return [session.name for session in sessions]

# @app.get('/sessions/find/{pattern}')
# async def find_sessions(pattern:str='*'):
#     sessions = search_sessions(pattern)
#     return [session.name for session in sessions]

@app.post('/session/setup/')
async def session_setup(session:Session, status_code=status.HTTP_201_CREATED):
    save_session(session)
    response= dict(session=session.session, 
    commands=['ssh mri20-dtn01',
    'conda activate /datastaging/conda_env/MMC', 
    f'mmc.py session transfer {session.session} --duration 16',
    f'mmc.py session preprocess {session.session} --duration 16'])
    return response

@app.get('/session/{sessionName}')
async def session_get(sessionName:str):
    _, session = load_session_from_file(sessionName)
    return session

@app.post('/session/{sessionName}/start')
async def session_start(background_tasks: BackgroundTasks, sessionName:str,duration:int=16,remove:bool=False):
    background_tasks.add_task(run_transfer, sessionName,duration,remove=remove)
    return {"message": f"{sessionName} started", 'session': sessionName }


@app.get('/session/{sessionName}/log')
async def session_log(sessionName:str, lineNumber:int=200) -> List[str]:
    sessionPath = find_session_directory(sessionName)
    return {'log':Path(sessionPath / 'session.log').read_text().split('\n')[-lineNumber:]}

@app.get('/session/{sessionName}/preprocess')
async def session_preprocess(background_tasks: BackgroundTasks,sessionName:str, scipion:bool=True, duration:int=16):
    background_tasks.add_task(preprocess, sessionName, scipion=scipion, duration=duration)
    return {"message": f"{sessionName} precessing started", 'session': sessionName }

@app.get('/scopes/', response_model=List[str])
async def list_scopes() -> List[str]:
    return list(settings.scopes.keys())

@app.get('/path/')
async def list_path(value:str):
    path = Path(value)
    root = Path(path.parent)
    remainder = path.name + '*'
    if root.exists:
        return root.glob(remainder)



