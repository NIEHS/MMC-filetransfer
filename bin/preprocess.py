#!/usr/bin/env python

##
# Login to biowulf.nih.gov and add these lines to your .bashrc file:

# Parameters:
##
# -source: Location of the raw data in the linux machine. Multiple locations can be specified using ',' (e.g. -source /gatan/X/GDH_20140916,/gatan/Y/GDH_20140916).
# -scope: Identifier for the scope. This parameter will be mapped into a folder on biowulf. The four possibilities are nih, atc, d256, d272, cmm, cmmk2.
# -sample: Identifier for the type of sample. This parameter will be mapped into a folder on biowulf (e.g. -sample GDH).
# -session: Identifier for the session, usually the sample name followed by '_' and the date (e.g. GDH_20140916). If the data is tomography, this identifier must contain the 'Tomo' prefix (e.g. Tomo_Bal_20140625).
# -remove: Remove the data from the linux machine once the transfer is complete.
# For quad-plots and 2D classification:
# nohup /home/bartesaghia/scripts/spy_daemon.py -source /gatan/X/GDH_20140916,/gatan/Y/GDH_20140916 -sample GDH -session GDH_20140916 -scope nih -remove -particle_rad 75 -extract_box 384 -thresholds 500,1000,0,0 &
##
##
# Parameters:
##
# -particle_rad: Radius of complex in Angstroms.
# -extract_box: Box size used to extract the particles.
# -thresholds: Particle number thresholds for processing.
# For quad-plots, 2D classification and 3D refinement:
# nohup /home/bartesaghia/scripts/spy_daemon.py -source /gatan/X/GDH_20140916,/gatan/Y/GDH_20140916 -sample GDH -session GDH_20140916 -scope nih -remove -particle_rad 75 -extract_box 384 -particle_mw 300 -particle_sym D3 -model /data/Cryoem/autoprocess_nih/GDH/GDH_OG_20140612/frealign/20140826_011259_GDH_OG_20140612_01.mrc -thresholds 500,1000,7500,1000 &
##
##
##
# Parameters:
##
# -particle_mw: Molecular weight of complex in KDa.
# -particle_sym: Symmetry of complex (e.g., C1, C2, C3, D2, D3, etc.).
# -particle_model: Initial model to be used for refinement. This should point to a location on biowulf and the dimensions of this volume should coincide with the value of the -extract_box option.

import subprocess as sub
import shutil
import time
import datetime
import argparse
import os
import sys
import matplotlib
import shlex
import json
from Transfer.settings import settings, groups
from Transfer.transfer import transfer
from Transfer.scipion_workflow import scipion_template

matplotlib.use('Agg')

class logLine:
    def __init__(self,group,session,pyp,scipion,timestamp):
        self.group = group
        self.session = session
        self.pyp = pyp
        self.scipion = scipion
        self.timestamp = float(timestamp)
    def to_string(self):
        return f'{self.group}\t{self.session}\t{self.pyp}\t{self.scipion}\t{self.timestamp}'

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Data transfer and processing daemons')
    parser.add_argument("-source", "--source", help='Location of data to transfer', required=True)
    parser.add_argument("-scope", "--scope", help='Name of scope (niehs,niehs_krios_epu,nih,atc,d256,d272)', default='niehs')
    parser.add_argument("-sample", "--sample", help='Name of sample', required=True)
    parser.add_argument("-session", "--session", help='Date YYYYMMDD.Today if blank')
    parser.add_argument("-particle_rad", "--particle_rad",default=0, help='Particle radius in A (TM only)', type=int)
    parser.add_argument("-scope_pixel", "--scope_pixel", help='Pixel size in A', type=float)
    parser.add_argument("-mag", "--magnification", help='magnification', type=int)
    parser.add_argument("-filesPattern","--filesPattern", help='extension for the frames files, i.e. *.tif, *_fractions.tiff, *.mrc', type=str, default=None)
    parser.add_argument("-t", "--time", help='How long should the script run in days', default=1, type=int)
    parser.add_argument("-dose_rate", "--dose_rate", help='Dose rate in e/A2', type=float)
    parser.add_argument("-extract_box", "--extract_box", help='Particle box in pixels (TM only)', type=int)
    parser.add_argument("-particle_sym", "--particle_sym", help='Symmetry of complex (e.g. C1, C3, D3, etc.) (TM only)', type=str, default='C1')
    parser.add_argument("-particle_mw", "--particle_mw", help='Molecular weight of complex in kDa (TM only)', type=float)
    parser.add_argument("-thresholds", "--thresholds", help='Daemon 2D and 3D thresholds (=5000,25000,7500,1000) (TM only)',
                        default='5000,25000,7500,1000')
    parser.add_argument("-group", "--group", help='Lab name as written on /data/Cryoem/autoprocess_niehs', type=str, required=True)
    parser.add_argument("-frames", "--frames", help='Number of frames per image', type=int, default=7)
    parser.add_argument("-model", "--model", help='Initial model for 3D refinement (has to match size of extract_box!) (TM only)', default=None)
    parser.add_argument("-local", "--local", help='Run data transfer only (do not start processing daemon on biowulf)',
                        action='store_true', default=False)
    parser.add_argument("-remove", "--remove", help='Remove files after succesful transfer and all reduntant files',
                        action='store_true', default=False)
    parser.add_argument("-scipion", "--scipion", help='Starts the scipion branch of the script',
                        action='store_true', default=False)
    parser.add_argument("-PYP", "--PYP", help='Starts PYP',
                        action='store_true', default=False)
    parser.add_argument("-mode", "--mode", help='spr or tomo', type=str, default='spr')
    parser.add_argument("-data_format", "--data_format", help='mrc or tif aligned micrographs', type=str, default='mrc')
    parser.add_argument("-data_bin", "-data_bin", help='binning factor the data and final micrographs', type=int, default=1)
    parser.add_argument("-chunk", "--chunk", help='How many files to bundle in one bundle, -1 to disble and bundle all', type=int, default=20)                
    args = parser.parse_args()


    if not args.scipion and not args.PYP:
        print('Please specify --scipion and/or --PYP')
        sys.exit()

    if args.PYP and not all([args.particle_rad,args.extract_box,args.scope_pixel,args.dose_rate]):
        print('With use with PYP, --paricle_rad, --extract_box, --scope_pixel and --dose_rate must be provided')
        sys.exit()        

    # create aliases
    if args.source[-1] != '/':
        sources = args.source + '/'
    else:
        sources = args.source
    sample = args.sample
    group = args.group

    if args.session:
        session = args.session + '_' + sample
    else:
        today = datetime.date.today().strftime("%Y%m%d_")
        session = today + sample

    if args.remove:
        print('WARNING: Files will be removed once they have been succesfully transferred.')
    # Defining the logs locations
    log_dir = os.path.join(settings.logs, session)
    for entry in [settings.logs, log_dir]:
        if not os.path.exists(entry):
            os.mkdir(entry)
    transfer_obj = transfer(args.source, delete=args.remove, logdir=log_dir, filesPattern=args.filesPattern)

    # check if scope value is valid
    if args.scope in set(['duke', 'unc', 'niehs', 'niehsk2', 'nci-b37', 'niehs_krios_epu', 'niehs_krios']):
        scope = '_' + args.scope.replace('k2', '')
    else:
        print('ERROR: -scope must be one of: duke, unc, niehs , niehsk2')
        sys.exit()
    # check arguments for particle picking
    if args.extract_box:
        if not args.particle_rad:
            print('ERROR: -particle_rad is also required.')
            sys.exit()
    
    if not args.scope_pixel:
        print('ERROR: --scope_pixel is required')

    # check arguments if using 3D refinement
    # if args.model:
    #     if not args.particle_rad or not args.extract_box or not args.particle_sym or not args.particle_mw or not args.scope_pixel:
    #         print('ERROR: -scope_pixel -particle_rad -extract_box -particle_sym and -particle_mw are required.')
    #         sys.exit()

    if 'niehs' in args.scope:
        ddn_raw_destination = os.path.join(settings.ddn_root, settings.ddn_raw_dir, group, session)
        for entry in ['/'.join(ddn_raw_destination.split('/')[:-1]), ddn_raw_destination]:
            if not os.path.isdir(entry):
                os.mkdir(entry)
                os.chmod(entry, 0o775)
                if settings.group is not None:
                    shutil.chown(entry, group=settings.group)

    if args.scipion:
        local_destination = os.path.join(settings.local_dir, group, session, 'raw')
        html_destination = os.path.join(settings.HTML, group, 'reports')
        for entry in ['/'.join(local_destination.split('/')[:-2]), '/'.join(local_destination.split('/')[:-1]), local_destination, '/'.join(html_destination.split('/')[:-1]), html_destination, os.path.join(settings.scipion_loc, group)]:
            if not os.path.isdir(entry):
                os.mkdir(entry)
                os.chmod(entry, 0o775)
                if settings.group is not None:
                    shutil.chown(entry, group=settings.group)
        phpfile = os.path.join('/'.join(html_destination.split('/')[:-1]), 'index.php')
        if not os.path.isfile(phpfile):
            shutil.copy(os.path.join(settings.template_files, 'index.php'), phpfile)
        workflow = scipion_template()

        workflow.set_values([
                ('import', 'filesPath', local_destination),
                ('import', 'timeout', int(args.time * 24 * 60 * 60)),
                ('import', 'gainFile', os.path.join(local_destination, 'gain.mrc') if not 'epu' in args.scope else None),
                # ('cryolo', 'boxSize', args.particle_rad),
                ('monitor', 'monitorTime', int(args.time * 24 * 60 * 60)),
                ('monitor', 'publishCmd', f'rsync -avL %(REPORT_FOLDER)s {html_destination}')
            ])

        if args.dose_rate:
            workflow.set_value('import', 'dosePerFrame', args.dose_rate)
        if args.scope_pixel:
            workflow.set_value('import', 'samplingRate', args.scope_pixel)
        if args.magnification:
            workflow.set_value('import', 'magnification', args.magnification)
        if args.filesPattern is not None:
            workflow.set_value('import', 'filesPattern', args.filesPattern)



        workflow.set_scope_defaults(args.scope)
        print(workflow.template['import']['filesPattern'])
        if 'epu' in args.scope and 'tif' in workflow.template['import']['filesPattern']:
            workflow.set_value('import', 'gainFile', os.path.join(local_destination, 'gain.tiff'))
        if workflow.check_completion():
            wf = workflow.save_template(os.path.join(log_dir, 'scipion_workflow.json'))
            if not args.local:
                print('All arguments for scipiont processing present.\nCreating Scipion project. Scheduling will occur after the first movies are transfered.')
                command = f"""{settings.scipion_path} python -m pyworkflow.project.scripts.create "{session}" "{wf}" "{os.path.join(settings.scipion_loc,group)}" """
                print(command)
                p = sub.run(shlex.split(command),stdout=sub.DEVNULL, stderr=sub.DEVNULL)
            #command = f"{settings.scipion_path} python -m pyworkflow.project.scripts.schedule {session}"
            #print(command)
            #p = sub.Popen(shlex.split(command),stdout=sub.DEVNULL, stderr=sub.DEVNULL, preexec_fn=os.setpgrp)
    # Connecting to globus
    if args.PYP:
        try:
            user = sub.check_output('globus whoami'.split(' '))
            print(f'Already logged into globus as {user}')
        except sub.CalledProcessError:
            print('Not connected to Globus, please sign in')
            sub.call('globus login'.split(' '))
            print('Successfully logged in to globus')

        # Defining the globlus locations
        biowulf_destination = os.path.join(settings.autoprocess, group, session)
        biowulf_destination = os.path.join(settings.root, settings.autoprocess, group, session)
        biowulf_raw_destination = os.path.join(settings.root, settings.raw_dir, group, session, 'raw')
        ddn_destination = os.path.join(settings.ddn_root_globus, settings.ddn_autoprocess, group, session)
        for entry in ['/'.join(ddn_destination.split('/')[:-1]), ddn_destination]:
            ep2_ls = sub.call(shlex.split('globus ls {0}:{1}'.format(settings.ddn_globus, entry)))
            if ep2_ls != 0:  # If destination directory doesn't exist, create it
                print(f'Destination directory not found creating destination directory {settings.ddn_globus}:{entry} ...')
                try:
                    sub.check_call(shlex.split(f'globus mkdir {settings.ddn_globus}:{entry}'))
                    print('Success.')
                except sub.CalledProcessError as err:
                    print(f'An error occured while creating directory\n{err.output}\nExiting...')
                    sys.exit(1)


        # create folders on biowulf using globus (will set group access attributes as the getfacl defaults)

        print('Creating directories on biowulf')
        if 'niehs' in args.scope:
            ssh_string = f"ssh {settings.biowulf}"
        elif 'nci-b37' in args.scope:
            ssh_string = ''
        sub.run(shlex.split(f"{ssh_string} mkdir -p {biowulf_raw_destination}"))
        if biowulf_destination != biowulf_raw_destination:
            sub.run(shlex.split(f"{ssh_string} mkdir -p {biowulf_destination}"))
            # try:
            #     sub.run(shlex.split(f"{ssh_string} ln -s {biowulf_raw_destination} {biowulf_destination}"))
            # except TypeError as err:
            #     print(err)

    # launch processing daemon on biowulf
        if not args.local:
            time_stamp = time.strftime('%Y%m%d_%H%M%S')
            sbatch_file = f'{time_stamp}_{session}_{group}_streampyp.batch'
            f = open(os.path.join(log_dir, sbatch_file), 'w')
            f.write('#!/bin/bash\n')
            f.write(f'#SBATCH --output={os.path.join(biowulf_destination, sbatch_file)}.out\n')
            f.write(f'#SBATCH --error={os.path.join(biowulf_destination, sbatch_file)}.err\n')
            f.write(f'#SBATCH --time={args.time}-00:00:00\n')
            f.write(f'#SBATCH --partition=norm\n')
            # f.write('#SBATCH --export=ALL\n')
            f.write(f'#SBATCH --mem=16g\n')
            f.write('#SBATCH --gres=lscratch:200\n')
            f.write(f'#SBATCH --job-name={session}\n')
            f.write('\nmodule load singularity\n')
            # f.write('export pypdaemon=pypdaemon\n')
            # f.write(f'export PYP_CONFIG={settings.pyp_config}\n')
            # pyp_command = f"singularity exec -B /gs10,/gs11,/gs12,/gs4,/gs5,/gs6,/gs7,/gs8,/gs9,/vf,/spin1,/data,/fdb,/home,/lscratch --no-home -B /home/{os.environ['USER']}/.ssh -B {settings.pyp_dir}:/opt/pyp /data/Cryoem/Development/Singularity/pyp.sif /opt/pyp/bin/run/pyp "
            pyp_command = f'{settings.pyp_dir}bin/streampyp -source {biowulf_raw_destination} '
            pyp_command += f"\\\n-session {session} \\\n-group {args.group} \\\n-target {os.path.join(settings.root, settings.autoprocess)} \\\n--mode {args.mode} \\\n-timeout {args.time} \\\n--data_bin {args.data_bin} \\\n--movie_weights \\\n--data_format {args.data_format} \\\n --gain_reference {os.path.join(biowulf_raw_destination,'gain.mrc')} \\\n"

            if args.particle_rad:
                pyp_command += f'-particle_rad {args.particle_rad} \\\n'
            if args.particle_sym:
                pyp_command += f'-particle_sym {args.particle_sym} \\\n'
            if args.particle_mw:
                pyp_command += f'-particle_mw {args.particle_mw} \\\n'
            if args.extract_box:
                pyp_command += f'-extract_box {args.extract_box} \\\n'
            if args.thresholds:
                pyp_command += f'-thresholds {args.thresholds} \\\n'
            if args.model:
                pyp_command += f'-model {args.model} \\\n'
            if args.scope_pixel:
                pyp_command += f'-scope_pixel {args.scope_pixel} \\\n'
            if args.dose_rate:
                pyp_command += f'-dose_rate {args.dose_rate} \\\n'
            # pyp_command += f' -frames {args.frames}'
            if args.scope == 'niehs':
                pyp_command += f"""--scope_voltage 200 \\\n--gain_rotation 3 \\\n--gain_flipv \\\n--fileset .tif,.tif.mdoc \\\n-symlinks """
            if args.scope == 'nci-b37':
                pyp_command += f"""--scope_voltage 300 \\\n--gain_flipv \\\n--fileset .tif,.tif.mdoc \\\n-symlinks """
            f.write(f'{pyp_command}')
            f.close()
            # transfer swarm file to biowulf
            
            com = f'scp {os.path.join(log_dir, sbatch_file)} {settings.helix}:{os.path.join(biowulf_destination, sbatch_file)}'
            if args.scope == 'nci-b37':
                com = f'cp {os.path.join(log_dir, sbatch_file)} {os.path.join(biowulf_destination, sbatch_file)}'
            print(com)
            sub.call(shlex.split(com))

            # submit to swarm
            jobname = session
            com = f"{ssh_string} sbatch {os.path.join(biowulf_destination, sbatch_file)}"
            sub.run(shlex.split(com))
            message = f'Job submitted to queue'
            print('\nStarting processing daemon on biowulf..')
            print(message)
        else:
            spy_command = 'none'
            jobnumber = 'none'
            message = 'none'


    #Append to general log
    preprocessLog = os.path.join(settings.logs, 'preprocess_history.txt')

    lines = []
    if os.path.isfile(preprocessLog):
        with open(preprocessLog,'r') as log:
            #open log and remove the current session if exist
            lines = [logLine(*l.split('\t')) for l in log.readlines()[1:] if not session in l]
    lines.append(logLine(group,session,args.PYP,args.scipion,time.time()))
    lines.sort(key=lambda x: x.timestamp)
    with open(preprocessLog,'w') as log:
        log.write(f'Group\tSession\tPYP\tScipion\ttimestamp\n')
        log.write('\n'.join([x.to_string() for x in lines]))
    
    if args.PYP:
        com = f'scp {preprocessLog} {settings.helix}:{os.path.join(settings.root,settings.autoprocess)}'
        sub.call(shlex.split(com))

        

    # Start transfer
    if 'niehs' in scope:
        nochange = 0
        scipion_started = False
        limit = 120
        timestamp = time.time()
        while nochange < limit:
            start = time.time()
            new_files = transfer_obj.list_source()
            is_transfer = False
            if new_files:
                nochange = 0
            else:
                nochange += 1
            if args.scipion is True:
                is_transfer = transfer_obj.transfer('copy', local_destination, label='scipion', auto_list=False, new_files=new_files, chunk=args.chunk)
                if not args.local and not scipion_started and nochange == 0:
                    print('Starting Scipion')
                    command = f"{settings.scipion_path} python -m pyworkflow.project.scripts.schedule {session}"
                    print(command)
                    p = sub.Popen(shlex.split(command),stdout=sub.DEVNULL, stderr=sub.DEVNULL, preexec_fn=os.setpgrp)
                    scipion_started = True
            if args.PYP is True:
                is_transfer = transfer_obj.transfer('bbcp', f'{settings.helix}:{biowulf_raw_destination}', label='pyp', auto_list=False, new_files=new_files, chunk=args.chunk)
            transfer_obj.remove()

            time_left = limit - (time.time() - start)
            if is_transfer:
                nochange = 0
                time_left = 0


            if time.time() - timestamp > 1800:
                timestamp = time.time()
                print('Synchronizing autoprocess into ddn')
                if args.PYP is True:
                    label_pyp = session
                    check_pyp = len(json.loads(sub.run(shlex.split(f"globus task list --format json --jmespath 'DATA[?status==`ACTIVE` && label==`{label_pyp}`]'"),capture_output=True).stdout)) == 0
                    if check_pyp:
                        com = f"globus transfer {settings.biowulf_globus}:{os.path.join(settings.root_globus,settings.autoprocess,group,session)} {settings.ddn_globus}:{ddn_destination} --recursive --preserve-mtime --label {label_pyp} -F json --notify failed,inactive --sync-level size  --jmespath 'task_id' --format=UNIX"
                        print('Stating globus transfer for PYP\n',com)
                        sub.run(shlex.split(com))
                print('Synchronizing raw data into ddn')
                if args.scipion is True:
                    lockfile = os.path.join(local_destination,'syncing.lock')
                    com = f'rsync -au {local_destination} {os.path.join(ddn_raw_destination)} ; rm {lockfile}'
                    print(com)
                    if not os.path.isfile(lockfile):
                        open(lockfile,'w').close()
                        sub.Popen(com, shell=True)
                    else:
                        print('Lock file found, skipping rsync')
                else:
                    label_raw = f'{session}_raw'
                    check_raw = len(json.loads(sub.run(shlex.split(f"globus task list --format json --jmespath 'DATA[?status==`ACTIVE` && label==`{label_raw}`]'"),capture_output=True).stdout)) == 0
                    if check_raw:
                        com = f"globus transfer {settings.biowulf_globus}:{os.path.join(settings.root_globus,settings.raw_dir,group,session)} {settings.ddn_globus}:{os.path.join(settings.ddn_root_globus,settings.ddn_raw_dir, group, session)} --recursive --preserve-mtime --label {label_raw} --notify failed,inactive --sync-level size  --jmespath 'task_id' --format=UNIX"
                        print('Stating globs transfer for raw data\n',com)
                        sub.run(shlex.split(com))
            print(f'No_change = {nochange}')
            if time_left > 0 and nochange < limit:
                print(f'Will look for files again in {round(time_left/60, 2)} min')
                time.sleep(time_left)
        else:
            print(f'Transfer finished, no new file was detected for {limit*120/60/60} hours, Removing write permission from raw data')
            sub.run(shlex.split(f'chmod -R 555 {ddn_raw_destination}'))

    elif 'nci-b37' in scope:
        nochange = 0
        limit = 120
        timestamp = time.time()
        while nochange < limit:
            start = time.time()
            new_files = transfer_obj.list_source()
            if new_files:
                nochange = 0
            else:
                nochange += 1
            # if args.scipion is True:
            #     transfer_obj.transfer('copy', local_destination, label='scpion', auto_list=False, new_files=new_files)
            if args.PYP is True:
                is_transfer = transfer_obj.transfer('copy', biowulf_raw_destination, label='pyp', auto_list=False, new_files=new_files)
            transfer_obj.remove()

            time_left = 120 - (time.time() - start)
            if is_transfer:
                nochange = 0
                time_left = 0

            if time.time() - timestamp > 1800:
                timestamp = time.time()
                print('Synchronizing autoprocess into ddn')
                if args.PYP is True:
                    com = f'globus transfer {settings.biowulf_globus}:{os.path.join(settings.root_globus,settings.autoprocess,group,session)} {settings.ddn_globus}:{ddn_destination} --recursive --preserve-mtime --label {session}_{nochange} -F json --notify failed,inactive'
                    print(com)
                    sub.Popen(shlex.split(com))
                print('Synchronizaing raw data into ddn')
                if args.scipion is True:
                    com = f'rsync -avu {local_destination} {os.path.join(ddn_raw_destination)}'
                    print(com)
                    sub.Popen(shlex.split(com))
                else:
                    com = f'globus transfer {settings.biowulf_globus}:{os.path.join(settings.root_globus,settings.raw_dir,group,session)} {settings.ddn_globus}:{os.path.join(settings.ddn_root_globus,settings.ddn_raw_dir, group, session)} --recursive --preserve-mtime --label {session}_raw_{nochange} -F json --notify failed,inactive'
                    print(com)
                    sub.Popen(shlex.split(com))
            print(f'No_change = {nochange}')
            if time_left > 0 and nochange < limit:
                print(f'Will look for files again in {round(time_left/60, 2)} min')
                time.sleep(time_left)
        else:
            print(f'Transfer finished, no new file was detected for {limit*120/60/60} hours, Removing write permission from raw data')
            sub.run(shlex.split(f'chmod -R 555 {ddn_raw_destination}'))
