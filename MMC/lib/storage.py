from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel
from pathlib import Path
from MMC.lib.transfer import async_transfer_local, bbcp, Movie, rsync
import signal
import subprocess as sub
import shlex
import yaml
import os
import logging

logger = logging.getLogger(__name__)

def is_nfs_available(path:Path):
    def handler(signum, frame):
        raise Exception("NFS is not available. skipping.")

    signal.signal(signal.SIGALRM,handler)
    signal.alarm(5)
    result = False
    try:
        sub.run(shlex.split(f'ls {str(path)}'))
        logger.info(f'NFS {path} is available')
        result = True
    except Exception as e:
        pass
        # logging.exception(e)
    finally:
        signal.alarm(0)
    return result

def create_directory(path):
    path.mkdir(exist_ok = True,parents=True)
    Path(path, 'raw').mkdir(exist_ok=True)

class StorageLocation(ABC,BaseModel):
    root:Path
    status: str
    session_path: Path|None =None

    @abstractmethod
    def transfer(self, fileList:List[Movie], destination:Path):
        ...

    @abstractmethod
    def make_session_dir(self):
        ...

    @abstractmethod
    def mkdir(self, directory:Path):
        ...

    def set_session_path(self,path:Path):
        self.session_path = self.root / path
        return self.session_path
    
    @property
    def session_raw_path(self):
        return self.session_path / 'raw'

class LocalStorageLocation(StorageLocation):

    async def transfer(self, fileList:List[Movie], destination:Path):
        return await async_transfer_local(fileList,destination,self.status)
    
    def make_session_dir(self):
        create_directory(self.session_path)

    def mkdir(self, directory: Path): 
        newDir = self.root /directory
        newDir.mkdir(exist_ok=True,parents=True)
        return newDir

class NSFStorageLocation(LocalStorageLocation):

    async def transfer(self, fileList:List[Movie], destination:Path):
        if is_nfs_available(destination.parent):
            return await super().transfer(fileList,destination)
        return fileList
    
    def make_session_dir(self):
        if is_nfs_available(self.session_path.parent):
            return super().make_session_dir()
    
    def mkdir(self, directory: Path):
        newDir = self.root /directory
        if is_nfs_available(newDir.parent):
            newDir.mkdir(exist_ok=True,parents=True)
        return newDir

class RemoteStorageLocation(StorageLocation):

    SSHstring:str

    async def transfer(self, fileList:List[Movie], destination:Path):
        return rsync(fileList,f'{self.SSHstring}:{str(destination)}', self.status)
    
    def make_session_dir(self):
        sub.run(shlex.split(f"ssh {self.SSHstring} mkdir -p {str(self.session_path / 'raw')}"))
    
    def mkdir(self, directory: Path):
        newDir = self.root /directory
        sub.run(shlex.split(f"ssh {self.SSHstring} mkdir -p {newDir}"))
        return newDir
    
    def sub_run(self, command: str) -> sub.CompletedProcess:
        command = f"""ssh {self.SSHstring} "{command}" """
        logger.info(command)
        return sub.run(shlex.split(command),stdout=sub.DEVNULL, stderr=sub.DEVNULL)
    
    def sub_Popen(self, command: str):
        command = f"""ssh {self.SSHstring} "{command}" """ 
        logger.info(command)
        return sub.Popen(shlex.split(command),stdout=sub.DEVNULL, stderr=sub.DEVNULL, preexec_fn=os.setpgrp)    

class RemoteHighPerformanceStorageLocation(RemoteStorageLocation):

    async def transfer(self, fileList:List[Movie], destination:Path,):
        return bbcp(fileList,f'{self.SSHstring}:{str(destination)}',self.status)


def load_storageLocations(file) -> List[StorageLocation]:
    storageLocationsFactory = {
        'local': LocalStorageLocation,
        'nfs': NSFStorageLocation,
        'remote': RemoteStorageLocation,
        'remote_bbcp': RemoteHighPerformanceStorageLocation,
    }

    with open(file) as f:
        storageLocations = yaml.safe_load(f)
    output_storageLocations = dict()
    for location, value in storageLocations.items():
        output_storageLocations[location] = storageLocationsFactory[value['storage_type']].parse_obj(value)
    return output_storageLocations


    
