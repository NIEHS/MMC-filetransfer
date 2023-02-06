import logging
from typing import List
from pathlib import Path

from fastapi import Request, status, Response, Depends, APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse 
from fastapi.templating import Jinja2Templates

from MMC.lib.session import Session, load_session_from_file, save_session, find_session_directory, filter_sessions
from MMC.preprocess.session import preprocess, run_transfer
# from MMC import setting
import auth

logger = logging.getLogger(__name__)

sessions= APIRouter(dependencies=[Depends(auth.get_current_active_user)])

templates = Jinja2Templates(directory="templates/sessions/")

@sessions.get('/sessions/find/')
async def find_sessions(group:str='*',project:str='*',session:str='*'):
    sessions = filter_sessions(group,project,session)
    return [session.name for session in sessions]

@sessions.get('/sessions/views/find/', response_class=HTMLResponse)
async def find_sessions(request:Request, group:str='*',project:str='*',session:str='*',):
    sessions = [session.name for session in filter_sessions(group,project,session)]
    return templates.TemplateResponse("find.html", {"request":request,"sessions": sessions})
    

@sessions.post('/session/setup/')
async def session_setup(session:Session, status_code=status.HTTP_201_CREATED):
    save_session(session)
    response= dict(session=session.session, 
    commands=['ssh mri20-dtn01',
    'conda activate /datastaging/conda_env/MMC', 
    f'mmc.py session transfer {session.session} --duration 16',
    f'mmc.py session preprocess {session.session} --duration 16'])
    return response

@sessions.get('/session/{sessionName}')
async def session_get(sessionName:str):
    _, session = load_session_from_file(sessionName)
    return session

@sessions.post('/session/{sessionName}/start')
async def session_start(background_tasks: BackgroundTasks, sessionName:str,duration:int=16,remove:bool=False):
    background_tasks.add_task(run_transfer, sessionName,duration,remove=remove)
    return {"message": f"{sessionName} started", 'session': sessionName }


@sessions.get('/session/{sessionName}/log')
async def session_log(sessionName:str, lineNumber:int=200) -> List[str]:
    sessionPath = find_session_directory(sessionName)
    return {'log':Path(sessionPath / 'session.log').read_text().split('\n')[-lineNumber:]}

@sessions.get('/session/{sessionName}/preprocess')
async def session_preprocess(background_tasks: BackgroundTasks,sessionName:str, scipion:bool=True, duration:int=16):
    background_tasks.add_task(preprocess, sessionName, scipion=scipion, duration=duration)
    return {"message": f"{sessionName} precessing started", 'session': sessionName }