from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel
from pathlib import Path
from MMC.lib.transfer import async_transfer_local, bbcp, Movie
import signal
import subprocess as sub
import shlex
import yaml

def is_nfs_available(path:Path):
    def handler(signum, frame):
        raise Exception("NFS is not available. skipping.")

    signal.signal(signal.SIGALRM,handler)
    signal.alarm(5)
    result = False
    try:
        path.iterdir()
        print(f'NFS {path} is available')
        result = True
    except Exception as e: 
        print(e)
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
    def mkdir(self):
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
    
    def mkdir(self):
        create_directory(self.session_path)

class NSFStorageLocation(StorageLocation):

    async def transfer(self, fileList:List[Movie], destination:Path):
        if is_nfs_available(destination.parent):
            return await async_transfer_local(fileList,destination,self.status)
        return fileList
    
    def mkdir(self):
        if is_nfs_available(self.session_path.parent):
            create_directory(self.session_path)

class RemoteStorageLocation(StorageLocation):

    SSHstring:str

    async def transfer(self, fileList:List[Movie], destination:Path,):
        return bbcp(fileList,f'{self.SSHstring}:{str(destination)}',self.status)
    
    def mkdir(self):
        sub.run(shlex.split(f"ssh {self.SSHstring} mkdir -p {str(self.session_path / 'raw')}"))

def load_storageLocations(file) -> List[StorageLocation]:
    storageLocationsFactory = {
        'local': LocalStorageLocation,
        'nfs': NSFStorageLocation,
        'remote': RemoteStorageLocation,
    }

    with open(file) as f:
        storageLocations = yaml.safe_load(f)
    output_storageLocations = dict()
    for location, value in storageLocations.items():
        output_storageLocations[location] = storageLocationsFactory[value['storage_type']].parse_obj(value)
    return output_storageLocations


    
