#!/usr/bin/env python

import os
from typing import List
from pathlib import Path
import shutil
import time
import re
import subprocess as sub
import shlex
from MMC import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False


def convert_gain(path:Path, destination:Path):
    init_path = path
    final_path = destination / 'gain.mrc'

    p = sub.run([os.path.join(settings.env.IMOD_BIN, 'dm2mrc'), str(init_path),
                 str(final_path)], stdout=sub.PIPE, stderr=sub.PIPE)
    print(f"Converting Gain: {' '.join(p.args)}")
    return final_path


class Movie:

    def __init__(self, path:Path, status=None, timestamp=None, delete=False):
        self.path = Path(path)
        # self.split_path()

        if status is None:
            self.status = []
        else:
            self.status = status
        if timestamp is None:
            self.timestamp = os.path.getctime(self.path)
        else:
            self.timestamp = timestamp
        self.delete = delete

    @property
    def root(self):
        return self.path.parent

    def __repr__(self) -> str:
        return f'Movie(path={self.path}, status={self.status} ,timestamp={self.timestamp}, delete={self.delete})'

    def __str__(self):
        return self.path.name

class Transfer:

    def __init__(self, source:Path, logdir, delete=False, filesPattern=None, gainReference=None):
        self.delete = delete
        self.source = Path(source)
        self.transfer_list = []
        self.gain_done = False

        self.logfile = os.path.join(logdir, 'transfer.list')
        self.logdir = logdir
        if os.path.isfile(self.logfile):
            self.load()
        self.filesPattern = self.set_filesPatterns(filesPattern)
        self.gainReference = self.set_gainReference(gainReference)



    def set_filesPatterns(self, filesPattern=None):
        if filesPattern is None:
            return ['*.mrc', '*.tif', '*.mdoc', '*/*/Data/*_fractions.mrc','*/*/Data/*_fractions.tiff']
        return [filesPattern, f'{filesPattern}.mdoc']

    def set_gainReference(self, gainReference=None):
        if gainReference is None:
            return ['*Ref*', '*Gain*', '*gain*', '*/*/Data/*_gain.tiff']
        return [gainReference]


    def load(self):
        # print('loading')
        with open(self.logfile, 'r') as file:
            lines = file.read().splitlines()
        for f in lines:
            f = f.split('\t')
            if 'gain' in f[0].lower() or 'Ref' in f[0]:
                self.gain_done = True
            self.transfer_list.append(Movie(f[0], status=[x for x in f[1].split(',') if x != ''], timestamp=float(f[2]), delete=str_to_bool(f[3])))

    def save(self):
        with open(self.logfile, 'w') as file:
            for f in self.transfer_list:
                status = ','.join(f.status)
                file.write(f'{str(f.path)}\t{status}\t{f.timestamp}\t{f.delete}\n')

    def list_source(self, minfiletime=60, filesPattern=None):
        files = []
        new_files = False
        files_done = [p.path.name for p in self.transfer_list]
        patterns = self.filesPattern
        for pattern in patterns:
            files +=  self.source.glob(pattern)
        for f in files:
            if f.name not in files_done and time.time() - f.stat().st_ctime > minfiletime:
                #Check if file is still being written if not there for 20+ minute
                if f.stat().st_ctime < 1200:
                    init_size = f.stat().st_size
                    time.sleep(1)
                    if init_size != f.stat().st_size:
                        continue
                m = Movie(path=f)
                m.delete = self.delete
                self.transfer_list.append(m)
                del m
                new_files = True
        self.transfer_list.sort(key=lambda x: x.timestamp)
        return new_files

    def get_subset(self,label:List,pool=5,no_meta=False):
        chunk_size=0
        subset=[]
        for f in self.transfer_list:
            if chunk_size == pool:
                break
            if not set(label).issubset(f.status):
                if f.path.suffix in ['.mdoc', '.tiff']:
                    chunk_size += 1
                if f.path.suffix == '.mdoc' and no_meta:
                    continue
                subset.append(f)
        return subset

    def process_gain(self, path:Path, destination:Path):
        if 'dm' in path.suffix:
            gain = convert_gain(path,destination) 
        else:
            gain = shutil.copyfile(path,destination / f'gain{path.suffix}')                
        self.transfer_list.append(Movie(str(gain),timestamp=os.path.getctime(path), status=['staging'] ,delete=False))
        self.gain_done = True

def bbcp(fileList:List[Movie], destination:Path, label:str):
    logger.info('Transfering with bbcp')
    command = f"""{settings.env.bbcp} -a -f -v {' '.join([f"'{str(f.path)}'" for f in fileList])} '{destination}'"""
    logger.debug(command)
    bbcp_process = sub.Popen(shlex.split(command),stdout=sub.PIPE, stderr=sub.STDOUT)
    os.set_blocking(bbcp_process.stdout.fileno(), False)
    pattern = re.compile(r'.*File\s.*/(.*)\screated.*')
    pattern1 = re.compile(r'.*File\s.*/(.*)\sappears.*')
    while True:
        line= bbcp_process.stdout.readline().decode()
        if bbcp_process.poll() is not None and not line:
            logger.info('bbcp transfer finished')
            break
        if not line:
            time.sleep(0.5)
            continue
        finds = re.findall(pattern1,line) + re.findall(pattern, line)
        for mic in finds:
            mic = next((x for x in fileList if x.path.name == mic and label not in x.status), None)
            if mic is not None:
                mic.status.append(label)
                logger.info(f'Transfered {mic.path.name}')

    return fileList

def rsync(fileList:List[Movie], destination:Path, label:str):
    logger.info('Transfering with rsync')
    command = f"""rsync -vogt --info=name2 {' '.join([f"'{str(f.path)}'" for f in fileList])} '{destination}'"""
    logger.debug(command)
    rsync_process = sub.Popen(shlex.split(command),stdout=sub.PIPE, stderr=sub.STDOUT)
    os.set_blocking(rsync_process.stdout.fileno(), False)
    pattern = re.compile(r'^([\w\.]+)\n$')
    pattern2 = re.compile(r'^([\w\.]+) is uptodate\n$') 
    while True:
        line= rsync_process.stdout.readline().decode()
        if rsync_process.poll() is not None and not line:
            logger.info('rsync transfer finished')
            break
        if not line:
            time.sleep(0.5)
            continue
        finds = re.findall(pattern, line) + re.findall(pattern2, line)
        for mic in finds:
            mic = next((x for x in fileList if x.path.name == mic and label not in x.status), None)
            if mic is not None:
                mic.status.append(label)
                logger.info(f'Transfered {mic.path.name}')

    return fileList

def copy(f, destination, label):
    if label in f.status:
        return f
    file = f.path
    try:
        new_loc = shutil.copy2(file, destination)
        logger.info(f'Copied {f.path.name}')
    except:
        logger.info(f'Could not locate file at {file}. ')
        new_loc = os.path.join(destination,f.path.name)
        if os.path.isfile(new_loc):
            logger.info('Found at destination')
        else:
            logger.info('Not found at destination, skipping for now.')
            return f
    if os.path.getsize(file) == os.path.getsize(new_loc):
        f.status += label
    return f

def remove_from_source(files_list, delete_status: list = ['staging']):
    for f in files_list:
        if f.delete is True and set(delete_status).issubset(f.status) and 'deleted' not in f.status:
            deleted= False
            while not deleted: 
                try:
                    Path(f.path.name).unlink()
                    deleted = True
                    f.status.append('deleted')
                except Exception as e:
                    logger.debug(f'Error removing {f.path.name}, {e}, trying again in 2 seconds')
                    time.sleep(2)
    
    return files_list

def update_source(files_list, source:Path):
    for f in files_list:
        f.path = source / f.path.name
    return files_list
        
async def async_transfer_local(fileList:List[Movie], destination:Path, label:str):
    tasks = [asyncio.to_thread(copy, f,destination,label=[label])for f in fileList]
    return await asyncio.gather(*tasks)

def check_file(file: Movie, source:Path, expected_frames:int) -> Movie:
    command = f"header {str(source/ file.path.name)}"
    command = sub.run(shlex.split(command),stdout=sub.PIPE, stderr=sub.PIPE)
    output = command.stdout.decode()

    pattern = re.compile(r'Start\scols,.*\d+\s+\d+\s+(\d+)\n')
    if 'ERROR:' in output:
        logger.info(f'File: {file} is corrupted')
        file.status.append('corrupted')
        return file
    m = re.search(pattern,output)
    result = m.group(1) if m else 0
    logger.debug(f'Frames= {result} in {file}')
    if int(result) != expected_frames:
        logger.info(f'File: {file} is incomplete')
        file.status.append('incomplete')
        return file

    file.status.append('checkOK')
    return file