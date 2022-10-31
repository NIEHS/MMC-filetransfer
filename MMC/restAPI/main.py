from pathlib import Path
from typing import List
from fastapi import FastAPI, status, Response, BackgroundTasks
from MMC.lib.groups import Group, save_groups
from MMC.lib.session import Session, load_session_from_file, save_session
from MMC import settings
import MMC.preprocess.groups
import logging

from MMC.preprocess.session import preprocess, run_transfer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
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
async def display_goup_info(name: str='__all__'):
    return MMC.preprocess.groups.display_group_info(name)

@app.post('/groups/add', status_code=status.HTTP_201_CREATED, )
async def add_group(group:Group,response:Response):
    if group.name in settings.groups:
        logger.info(f'Group {group.name} already exists')
        response.status_code = status.HTTP_208_ALREADY_REPORTED
        return settings.groups[group.name]
    settings.groups[group.name] = group
    save_groups(settings.groups, settings.groups_file)
    return group

@app.put('/groups/update')
async def update_group(group:Group,response:Response):
    settings.groups[group.name] = group
    save_groups(settings.groups, settings.groups_file)
    return group

@app.post('/session/setup/')
async def session_setup(session:Session, status_code=status.HTTP_201_CREATED):
    save_session(session)
    return session

@app.get('/session/{sessionName}')
async def session_get(sessionName:str):
    _, session = load_session_from_file(sessionName)
    return session

@app.post('/session/{sessionName}/start/')
async def session_start(background_tasks: BackgroundTasks, sessionName:str,duration:int=16,remove:bool=False):
    background_tasks.add_task(run_transfer, sessionName,duration,remove=remove)
    return {"message": f"{sessionName} started", 'session': sessionName }


@app.get('/session/{sessionName}/log')
async def session_log(sessionName:str) -> List[str]:
    return Path(settings.env.logs / sessionName / 'session.log').read_text().split('\n')[-200:]

@app.get('/session/{sessionName}/preprocess/')
async def session_preprocess(background_tasks: BackgroundTasks,sessionName:str, scipion:bool=True, duration:int=16):
    background_tasks.add_task(preprocess, sessionName, scipion=scipion, duration=duration)
    return {"message": f"{sessionName} precessing started", 'session': sessionName }



