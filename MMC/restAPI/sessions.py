import logging
import os
import signal
import json
import subprocess
from datetime import datetime
from typing import List
from pathlib import Path

from fastapi import Request, status, Response, Depends, APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from MMC.lib.session import Session, load_session_from_file, save_session, find_session_directory, filter_sessions
from MMC.preprocess.session import preprocess, run_transfer
# from MMC import setting
from MMC.restAPI import auth

logger = logging.getLogger(__name__)

sessions= APIRouter(dependencies=[Depends(auth.get_current_active_user)])

templates = Jinja2Templates(directory=Path(__file__).parent / "templates" / "sessions")

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


# --- Independent transfer subprocess helpers ---

def _pid_file_path(sessionName: str) -> Path:
    return find_session_directory(sessionName) / 'transfer.pid'

def _read_pid_file(pid_path: Path):
    """Return parsed PID file dict, or None if it does not exist or is unreadable."""
    if not pid_path.exists():
        return None
    try:
        return json.loads(pid_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

def _is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


@sessions.post('/session/{sessionName}/transfer')
async def session_transfer_start(
    sessionName: str,
    duration: float = 16,
    cluster: bool = False,
    remove: bool = False,
    checkFiles: bool = False,
    noStaging: bool = False,
    noLongTerm: bool = False,
    emailLevel: str = 'all',
):
    pid_path = _pid_file_path(sessionName)
    existing = _read_pid_file(pid_path)
    if existing and _is_process_alive(existing['pid']):
        raise HTTPException(status_code=409, detail=f"Transfer already running with PID {existing['pid']}")

    cmd = [
        'mmc.py', 'session', 'transfer', sessionName,
        '--duration', str(duration),
        '--emailLevel', emailLevel,
    ]
    if cluster:
        cmd.append('--cluster')
    if remove:
        cmd.append('--remove')
    if checkFiles:
        cmd.append('--checkFiles')
    if noStaging:
        cmd.append('--noStaging')
    if noLongTerm:
        cmd.append('--noLongTerm')

    proc = subprocess.Popen(
        cmd,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    pid_data = {
        'pid': proc.pid,
        'started_at': datetime.utcnow().isoformat(),
        'args': {
            'duration': duration,
            'cluster': cluster,
            'remove': remove,
            'checkFiles': checkFiles,
            'noStaging': noStaging,
            'noLongTerm': noLongTerm,
            'emailLevel': emailLevel,
        }
    }
    pid_path.write_text(json.dumps(pid_data, indent=2))
    logger.info(f"Launched transfer for {sessionName} with PID {proc.pid}")
    return {'status': 'running', 'pid': proc.pid, 'started_at': pid_data['started_at']}


@sessions.get('/session/{sessionName}/transfer/status')
async def session_transfer_status(sessionName: str):
    pid_path = _pid_file_path(sessionName)
    data = _read_pid_file(pid_path)
    if data is None:
        return {'status': 'not_started'}
    if _is_process_alive(data['pid']):
        return {'status': 'running', 'pid': data['pid'], 'started_at': data['started_at'], 'args': data['args']}
    return {'status': 'stopped', 'pid': data['pid'], 'started_at': data['started_at'], 'args': data['args']}


@sessions.delete('/session/{sessionName}/transfer')
async def session_transfer_stop(sessionName: str):
    pid_path = _pid_file_path(sessionName)
    data = _read_pid_file(pid_path)
    if data is None:
        raise HTTPException(status_code=404, detail="No transfer PID file found")
    pid = data['pid']
    if not _is_process_alive(pid):
        raise HTTPException(status_code=409, detail=f"Process {pid} is not running")
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        raise HTTPException(status_code=409, detail=f"Process {pid} disappeared before SIGTERM")
    logger.info(f"Sent SIGTERM to transfer process {pid} for session {sessionName}")
    return {'status': 'stopping', 'pid': pid}