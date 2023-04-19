from copy import copy
from typing import List
import time
import traceback
import logging
from pathlib import Path
from MMC.lib.email import send_email
from MMC.lib.logger_settings import add_log_handlers
from MMC.lib.transfer import Movie, Transfer, check_files, remove_from_source, update_source
from MMC.lib.session import save_session, load_session_from_file, Session
from MMC.lib.scipion_workflow import scipion_template, new_scipion_template

from MMC import settings


logger = logging.getLogger(__name__)

def initiate_session(session: Session):
    session= Session.parse_obj({k:v for k,v in session.items() if v is not None})
    save_session(session)

async def run_transfer(session:str, duration:float=16, cluster:bool=False, remove:bool=False, checkFiles:bool=False, noStaging:bool=False, noLongTerm:bool=False, emailLevel:str='all'):
    
    nochange = 0
    nochange_sleep = 120
    idle_time_notification = 45
    pool = 5
    restart = True
    duration_in_seconds = duration*60*60
    email_send_timeout = 90
    init_email_sent_time = time.time() - 90*60
    email_sent_time = copy(init_email_sent_time)
   

    start_time = time.time()
    file, session = load_session_from_file(session)
    add_log_handlers(file.parent / 'session.log')
    # Adding start time to session file
    if session.status == 'created':
        session.set_startTime()
    session.status = 'started'
    save_session(session)
    transfer_obj = Transfer(session.sourceDir, delete=remove, logdir=file.parent, filesPattern=session.filesPattern, gainReference=session.gainReference)

    logger.info('Initiating transfer')
    try:
        transfer_locations = []


        if not noStaging:
            transfer_locations.append(settings.storageLocations['staging'])
        if not noLongTerm:
            transfer_locations.append(settings.storageLocations['longTerm'])
        else:
            logger.warning(f'Will not automatically move file to long term storage!')
        if cluster:
            transfer_locations.append(settings.storageLocations['cluster'])
        
        assert len(transfer_locations) != 0, f'Need to specify at least one location {settings.storageLocations.keys()}'

        for location in transfer_locations:
            location.set_session_path(session.specific_path)
            location.make_session_dir() 
        
        while not transfer_obj.gain_done and not session.gainCorrected:
            logging.info('Looking for gain reference.')
            gainfiles = []
            for pattern in transfer_obj.gainReference:
                logger.debug(f'Checking gain Pattern {pattern}')
                if Path(pattern).is_absolute:
                    pattern = Path(pattern)
                    if pattern.exists():
                        gainfiles += [pattern]
                        break
                gainfiles += list(session.source.glob(str(pattern)))
            if gainfiles:
                gainfiles.sort(key= lambda x: x.stat().st_ctime)
                transfer_obj.process_gain(gainfiles[0], transfer_locations[0].session_raw_path)
                break
            logger.info(f'Gain reference with patterns {transfer_obj.gainReference} not found, waiting 2 min.')
            time.sleep(120)
        session.status = 'transferring'
        save_session(session)
        while True:
            idle_time = nochange*nochange_sleep/60
            if emailLevel == 'all' and idle_time >= idle_time_notification and time.time() - email_sent_time >= email_send_timeout*60:
                email_sent_time = time.time()
                logger.warning(f'Sending email.')
                send_email(
                    title= f'WARNING: {session.session} No files found in {idle_time:.0f} mintues', 
                    message= f'Something may be wrong with data collection.\n\n{session.to_string()}',
                    )
            if time.time() - start_time >= duration_in_seconds:
                logger.info(f'Time limit of {duration}h has been reached')
                break

            new_files = transfer_obj.list_source()
            if not new_files and not restart:
                nochange += 1
                logger.info(f'No files were found in the last {idle_time:.1f} minutes. Will look for files again in {nochange_sleep/60:.1f} min')
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
                    logger.info(f'Moving files to {location.status} {location.session_raw_path}.')
                    to_transfer = transfer_obj.get_subset([location.status],pool=pool)
                    if len(to_transfer) == 0:
                        continue
                    results = await location.transfer(to_transfer,location.session_raw_path)
                    if checkFiles and location.status =='staging':
                        results = await check_files(results,source=location.session_raw_path, expected_frames=session.frameNumber, action='move')
                    if transfer_obj.delete and location.status =='staging':
                        results = remove_from_source(results,delete_status=[location.status])
                    if set(['staging','deleted']).issubset(set(location.status)):
                        results = update_source(results,location.session_raw_path)
                    transfer_obj.tansfer_list = set(transfer_obj.transfer_list).update(results)
                    transfer_obj.save()
        session.status = 'completed'
    except KeyboardInterrupt:
        logger.info('Interrupting')
        session.status = 'killed'
    except Exception as err:
        logger.exception(err)
        session.status = 'error'
        if emailLevel == 'all':
            send_email(
                title= f'ERROR: {session.session}', 
                message= f'The file transfer has terminated unexpectedly.\n\n{session.to_string()}\n\nTraceback:\n{traceback.format_exc()}',
                )
    finally:
        logger.info('Saving and exiting.')
        session.set_endTime()
        session.set_duration()
        session.numberOfMovies = len([f for f in transfer_obj.transfer_list if not '.mdoc' in f.path.name and not 'gain' in f.path.name]) - 1
        save_session(session)
        transfer_obj.save()
        if session.status == 'completed' and emailLevel == 'all':
            send_email(
                title= f'COMPLETED: {session.session} is finished.', 
                message= session.to_string(),
                contacts= session.project_obj.emailList
                )
        for location in transfer_locations:
            await location.transfer([Movie(file, delete=False),Movie(transfer_obj.logfile,delete=False)],location.session_path)

async def preprocess(session: str, scipion:bool=True, duration:float=16):
    
    file, session = load_session_from_file(session)

    if scipion:
        storage_location = settings.storageLocations['scipion']
        logger.info('Creating scipion workflow')
        html_destination = settings.env.HTML / session.group / 'reports'
        phpFile = html_destination.parent / 'index.php'
        storage_location.mkdir(phpFile.parent)
        await storage_location.transfer([Movie(Path(settings.env.template_files,'index.php'))], phpFile)
        raw_path = settings.storageLocations['staging'].set_session_path(session.specific_path) / 'raw'
        workflow = scipion_template()

        workflow.set_values([
                ('import', 'filesPath', str(raw_path)),
                ('import', 'timeout', 240*60),
                ('import', 'gainFile', session.get_gain_file(raw_path)),
                ('monitor', 'monitorTime', int(duration * 60)),
                ('monitor', 'publishCmd', f'rsync -avL %(REPORT_FOLDER)s {html_destination}'),
                ('import', 'dosePerFrame', session.totalDose/ session.frameNumber),
                ('import', 'samplingRate', session.pixelSize),
                ('import', 'magnification', session.magnification),
            ])
        workflow.set_scope_defaults(session.scope)
        if not workflow.check_completion():
            return 
        wf = workflow.save_template(file.parent/'scipion_workflow.json')
        scipion_session_directory = storage_location.mkdir(session.specific_path)
        logger.info('All arguments for scipion processing present.\nCreating Scipion project. Scheduling will occur after the gain is transfered.')
        command = f"""{str(settings.env.scipion_path)} python -m pyworkflow.project.scripts.create "{session.session}" "{wf}" "{str(scipion_session_directory.parent)}" """
        storage_location.sub_run(command)
        time.sleep(5)
        while True:
            _, session = load_session_from_file(session.session)
            if len(list(raw_path.glob('gain*'))) > 0 or session.gainCorrected:
                logger.info('All of scipion requirements are satisfied. Starting preprocessing.')
                command = f"{str(settings.env.scipion_path)} python -m pyworkflow.project.scripts.schedule {session.session}"
                p = storage_location.sub_Popen(command)   
                return
            logger.info('Waiting 2 min for gain file to be transfered.')
            time.sleep(120) 

async def checkFiles(session:str, directory:str, force:bool=False, action:str='move'): 
    file, session = load_session_from_file(session)
    transfer_obj = Transfer(session.sourceDir, logdir=file.parent, filesPattern=session.filesPattern, gainReference=session.gainReference)
    to_check = transfer_obj.total_files
    location = settings.storageLocations[directory]
    location.set_session_path(session.specific_path)
    directory = location.session_raw_path / 'corrupted'

    logger.info(f'Found {to_check} files to check')
    total=0
    transfer_list = copy(transfer_obj.transfer_list)
    pool_limit = 50
    while transfer_list:
        fileList = []
        while len(fileList) < pool_limit and transfer_list:
            file = transfer_list.pop()
            if force:
                file.status = list(set(file.status).difference(['checkOK','incomplete','corrupted']))
            if any(['.mdoc' in file.path.name,'Ref' in file.path.name,'gain' in file.path.name, 'checkOK' in file.status, 'corrupted' in file.status, 'incomplete' in file.status]):
                total +=1
                continue
            fileList.append(file)
            total += 1

        results = await check_files(fileList,source=location.session_raw_path, expected_frames=session.frameNumber, action=action)
        transfer_obj.tansfer_list = set(transfer_obj.transfer_list).update(results)
        transfer_obj.save()
        logger.info(f'Processed {total}/{to_check} files. {total/to_check*100:.1f} % done.')
    
    session.corrupted = transfer_obj.total_corrupted_files
    logger.info(f'Found {session.corrupted} corrupted or incomplete files.')
    save_session(session)

async def new_preprocess(session: str, scipion:bool=True, duration:float=16, movieBin:float=1.0, particleSize:int|None=None, gpus:List=[0,1,2,3], trigger2D=30_000):
    
    file, session = load_session_from_file(session)

    if scipion:
        storage_location = settings.storageLocations['new_scipion']
        logger.info('Creating scipion workflow')
        html_destination = settings.env.HTML / session.group / 'reports'
        html_good_destination = settings.env.HTML / session.group / 'reports_good'
        phpFile = html_destination.parent / 'index.php'
        settings.storageLocations['staging'].mkdir(phpFile.parent)
        await settings.storageLocations['staging'].transfer([Movie(Path(settings.env.template_files,'index.php'))], phpFile)
        raw_path = settings.storageLocations['niehs_cluster'].set_session_path(session.specific_path) / 'raw'
        workflow = new_scipion_template()

        workflow.set_values([
                ('import', 'filesPath', str(raw_path)),
                ('import', 'timeout', 240*60),
                ('import', 'gainFile', session.get_gain_file(raw_path)),
                ('monitor', 'monitorTime', int(duration * 60)),
                ('monitor', 'publishCmd', f'rsync -aL %(REPORT_FOLDER)s mri20-dtn01:{html_destination}'),
                ('monitorGood', 'monitorTime', int(duration * 60)),
                ('monitorGood', 'publishCmd', f'rsync -aL %(REPORT_FOLDER)s mri20-dtn01:{html_good_destination}'),
                ('import', 'dosePerFrame', session.totalDose/ session.frameNumber),
                ('import', 'samplingRate', session.pixelSize),
                ('import', 'magnification', session.magnification),
                ('trigger', 'outputSize', trigger2D),
                ('motioncor','binFactor', movieBin)
            ])
        workflow.set_scope_defaults(settings.scopes[session.scope])
        workflow.set_particle_size(particleSize)
        workflow.set_gpu_ids(gpus_list=gpus)
        if not workflow.check_completion():
            return 
        workflow.update_full_template()
        wf = workflow.save_template(file.parent/'scipion_workflow.json')
        scipion_session_directory = storage_location.mkdir(session.specific_path)
        await settings.storageLocations['longTerm'].transfer([Movie(wf)],scipion_session_directory)
        logger.info('All arguments for scipion processing present.\nCreating Scipion project. Scheduling will occur after the gain is transfered.')
        command = f"""{'/ddn/gs1/project/cryoemCore/autoprocess/Scipion/ScipionUserData/scipion.sh'} python -m pyworkflow.project.scripts.create "{session.session}" "{scipion_session_directory/ wf.name}" "{str(scipion_session_directory.parent)}" """
        storage_location.sub_run(command)
        time.sleep(5)
        while True:
            _, session = load_session_from_file(session.session)
            if len(list(raw_path.glob('gain*'))) > 0 or session.gainCorrected:
                logger.info('All of scipion requirements are satisfied. Starting preprocessing.')
                command = f"{'/ddn/gs1/project/cryoemCore/autoprocess/Scipion/ScipionUserData/scipion.sh'} python -m pyworkflow.project.scripts.schedule {session.session}"
                p = storage_location.sub_Popen(command)   
                return
            logger.info('Waiting 2 min for gain file to be transfered.')
            time.sleep(120)