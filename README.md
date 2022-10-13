# MMC file transfer and preprocessing

This python package is mainly used to transfer raw data from cryo-TEM data collection from the microscope computer to staging, long-term and computing cluster areas and simplify the preprocessing of the data. It organizes the data into groups and projects during filetransfer.

This new version also keeps track of data collection parameters and saves them alongside the data for future reference. This information is espacially important when writing up the materials and methods section of manuscripts.

## New to this version

- New groups have to be added to a master file before use. This will prevent group creation from typos
- Automatic emails to the employees of the cryo-em facilities upon error or when the data stream is interrupted
- Automatic emails to the project leads about the details of their data collection
- Revised command-line interface
- New data collection session organization. Now organized into groups/project/session from groups/session. Extramural and external collaborators now have their dedicated storage areas.
- Multiple files transfered concurrently instead of one after the other. This should result in faster transfer speeds.
- Added extra check to ensure the files are fully written before being transfered.

## Installation

Other dependencies:
- [IMOD](https://bio3d.colorado.edu/imod/). Required. Follow the installation instructions
- [bbcp](https://www.slac.stanford.edu/~abh/bbcp/). Just download the executable for your architecture. Not needed if not running remote transfers.
- [Scipion](https://scipion.i2pc.es/). Optional. Only if scipion preprocessing is going to be used.

Create a new python 3.10 anaconda environment
```
conda create -n MMC python==3.10
conda activate MMC
```

Clone the repository and install.
```
git clone https://github.com/NIEHS/MMC-filetransfer.git
cd MMC-filetransfer
pip install -e .
```

## Initial Setup

To get started, an enviroment files needs to be created. There is a template file in the repository.

1. Generate the `.env` file from the template.
    ```
    cd config
    cp env-template .env
    ```
2. Open the file in a text editor and fill the values. Below is an explanation of each value
    ```
    # executables
    bbcp = '' #Full path to bbcp 
    IMOD_BIN = '/usr/local/IMOD/bin/' #Full path to the IMOD binaries.
    scipion_path = '/usr/local/scipion-3.0/scipion3' #Full path to the scipion3 executable

    # Local area to store the logs
    logs = '' #Where the initial information about the transfer session is saved
    log_level = 'INFO' #Set the log_level to 'INFO' or 'DEBUG'

    # Emails
    sender_email = '' #Who is sending the email notifications
    smtp_server = '' #domain of the stmp server
    smtp_port = #Port used by the server

    # Scipion
    HTML = ''  #Path to where the scipion static html reports should be placed
    ```
3. Setup storage locations. Open `config/storageLocations.yaml` in a text editor.
    
    There are 4 locations that can be set up. staging, longTerm, cluster, and scipion.
    ```yaml
    staging: #required
      status: staging
      root: /datastaging/data/gatan_movies #Set to the path where the staging are is. It is recommended to use a highly-available local path close to the microscope.
      storage_type: local
    longTerm:
      status: longTerm
      root: /ddn/cryoemCore/data/projects_niehs #Change path to the long-term location
      storage_type: nfs #NFS is similar to local but is a mounted network share. The transfer will ensure that the nfs drive is available before transfering the files.
    cluster:
      status: cluster
      root: /data/Cryoem/projects_niehs #Change path to the cluster location
      SSHstring: helix.nih.gov #Change to the ssh hostname of your cluster
      storage_type: 'remote' #Will use bbcp to transfer the files to the cluster
    scipion:
      status: scipion
      root: /data-edison/Scipion/
      SSHstring: edison
      storage_type: remote
    ```

4. Set up mailing list for warnings and errors.
    This mailing list is for staff users to warn about errors and idling of the files transfers.
    The list should be put in `config/contact_emails.txt`. One email per line:
    ```
    jo@blo.com
    jane@doe.gov
    hello@world.net
    ```

# Usage

## One-time setup for each users

If you are planning on using remote ssh-based transfers, please [set up an ssh key](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-2) for passwordless transfers. 

If `scipion` is set as `storage_type: remote`, an ssh key to that host will also be required.

## Activating the environment

```shell
$ conda activate MMC
(MMC)$ 
```

## Command-line interface basics

The only executable for this package is `mmc.py`. To bring up the general help menu, do not use any argument.

```shell
$ mmc.py
Welcome to the MMC command line interface.

Below is a list of available commands with their associated subcommands.

    groups
       |-> add             (Add new group)
       |-> list            (List all groups or specific group)
       |-> add_project     (Add project to the specific group)
       |-> add_emails      (Add emails to a project)
   session
       |-> setup           (Initiates the session)
       |-> transfer        (Starts file transfer to staging and long-term storage)
       |-> preprocess      (Start the preprocessing
```
There are 2 main commands, groups and session and then sub-commands with a summary of the function. To learn more about a sub-command, you can bring up the help menu with `mmc.py mainCommand subCommand -h`:
```
#Example
$ mmc.py groups add -h
usage: Add new group [-h] name {NIEHS,NICE,Collaborations}

positional arguments:
  name                  Name of the group
  {NIEHS,NICE,Collaborations}
                        Affiliation for the group

options:
  -h, --help            show this help message and exit
```

## Editing groups

Groups can be added/edited either via the command-line interface or by manually editing the `config/groups.yaml` file.

### Add Group
To add a group, provide a name and an affiliation:
- Name should not contain spaces
- Affiliation options:
    - NIEHS: For local NIEHS users
    - NICE: For intramural users part of the NICE consortium
    - Collaborations: For external collaborators
```
# Example
$ mmc.py BorgniaM NIEHS
{'name': 'BorgniaM', 'affiliation': 'NIEHS'}
Adding name='BorgniaM' affiliation='NIEHS' projects=[]
```

### Add project to group
To add a project into an existing group, the following will need to be provided:
- Name of the group to which the projects is to be added
- Name of the project
- A list of emails associated to that project to send notification and summary about the data collection session

```
# Example
$mmc.py groups add_project BorgniaM Project1 -emails student@univ.gov trainee@nih.gov
{'group': 'BorgniaM', 'name': 'Project1', 'emails': ['student@univ.gov', 'trainee@nih.gov']}
```

### Add emails to project
To add emails to an already existing project
- The group and project together, separated by a point (i.e. BorgniaM.Project1)
- The list of emails as for the previous command

```
# Example
$ mmc.py groups add_emails BorgniaM.Project1 -emails newTrainee@nih.gov anotherPerson@nih.gov
{'project': 'BorgniaM.Project1', 'emails': ['newTrainee@nih.gov', 'anotherPerson@nih.gov']}
############################################################
Group:          BorgniaM
Affiliation:    NIEHS
Pojects:
     Project1: student@univ.gov, trainee@nih.gov, newTrainee@nih.gov, anotherPerson@nih.gov
############################################################
```

### List groups
There is a command to list all groups or a specific one.
- Optionally provide a name to list a single group, otherwise list all

```
# Example
$ mmc.py groups list
{'name': '__all__'}
############################################################
Group:          BorgniaM
Affiliation:    NIEHS
Pojects:
     Project1: student@univ.edu, trainee@nih.gov, newTrainee@nih.gov, anotherPerson@nih.gov
     Project2: student2@univ.edu, trainee@nih.gov
############################################################
############################################################
Group:          testing
Affiliation:    NIEHS
Pojects:
     test_transfer: jonathan.bouvette@nih.gov
     project2: bla@bla.com, bla3@nih.gov
############################################################
```

```
#Example 2
$ mmc.py groups list -name BorgniaM
{'name': '__all__'}
############################################################
Group:          BorgniaM
Affiliation:    NIEHS
Pojects:
     Project1: student@univ.edu, trainee@nih.gov, newTrainee@nih.gov, anotherPerson@nih.gov
     Project2: student2@univ.edu, trainee@nih.gov
############################################################
```

### Groups file synthax
The synthax of the `groups.yaml` is the following:
```yaml
- name: GroupNameHere
  affiliation: NIEHS,Collaboration or NICE
  projects:
    - name: ProjectNameHere
      emailList: [email@email.com, email2@email.com, ...]
    - name: OtherProjectName
      emailList: []
- name: OtherGroupHere
  ...
```

## Running a session

### Session setup
Before running a session, it has to be created. There is a specific command to set up a new session.

Many arguments need to be provided to this command. The touroughness helps in ensuring proper bookkeeping about the data collection sessions. Especially at the time of writing the materials and methods section of a new manuscript.

To learn all the arguments to the setup command, please use `mmc.py session setup -h`
```
# Minimal command example
mmc.py session setup -source /mnt/gatan_Raid_X/test_pyp/ \
                     -sample ApoferritinSample1
                     -group testing \
                     -project test_transfer \
                     -scope niehs_arctica \
                     -magnification 45000 \
                     -pixelSize 0.9321 \
                     -totalDose 50 \
                     -frameNumber 60 \
                     -detectorCounts 8.3
```
The following detailed examples show how the gain reference and the files pattern can be specificed in case multiple sessions are in the same source directory.
```
# More detailed command example
mmc.py session setup -source /mnt/gatan_Raid_X/test_pyp/ \
                     -sample ApoferritinSample1
                     -group testing \
                     -project test_transfer \
                     -scope niehs_arctica \
                     -magnification 45000 \
                     -pixelSize 0.9321 \
                     -totalDose 50 \
                     -frameNumber 60 \
                     -detectorCounts 8.3 \
                     -filesPattern *.tif \ 
                     -gainReference /mnt/gatan_Raid_X/test_pyp/CountRef_20210915_ES1-0901-1_000.dm4a

{'source': '/mnt/gatan_Raid_X/test_pyp/', 'group': 'testing', 'project': 'test_transfer', 'sample': 'test2', 'scope': 'niehs_arctica', 'magnification': '45000', 'pixelSize': 0.9321, 'totalDose': 50.0, 'frameNumber': 60, 'detectorCounts': 8.3, 'mode': 'spr', 'tiltAngleOrScheme': '0', 'filesPattern': '*.tif', 'gainReference': '/mnt/gatan_Raid_X/test_pyp/CountRef_20210915_ES1-0901-1_000.dm4', 'date': None}
Created settings file for session 20221011_ApoferritinSample1 at /datastaging/data/mmc/20221011_test2/settings.yaml
```
Note the output of the command: The session name is `20221011_ApoferritinSample1`

The edit the run, the command can be rerun. Alternatively, the yaml file can be modified directly with a text editor.

### Run the file transfer for a session
After creation, a session can be run for preprocessing and file transfer. The command for starting the file transfer is `mmc.py session transfer`. The following arguments will need to be provided:
- The session name
- The expected duration of the run in hours
- Whether or not to move the raw data to the cluser (optional)

```
$ mmc.py session transfer 20221011_ApoferritinSample1 -duration 16
```
**It is recommended to use tmux or screen to run this command**

### Start the Scipion preprocessing
The created session can also be preprocessed with Scipion automatically with the `mmc.py session preprocess` command. The command will create a scipion project for the session and initiate the project when the gain reference file has been transfered.

```
$ mmc.py session preprocess 20221011_ApoferritinSample1 -duration 16
```

## Directory Structure and files

### Master directory
One of the main areas to find data and log files is in the `log` directory specified in the `.env` file. In tha area you will find:

- A master log file for everything that happened in the past 14 days, located in `logs/mmc.log`
- For existing session as directory in `YYYMMDD_sampleName`.
  - That directory contains the session parameters as `session.yaml`
  - The session log file as `session.log`
  - The list of files that were transfered in csv format as `transfer.list`
  - If scipion preprocessing was run, the submitted scipion workflow template as `workflow_template.json`

### Sessions raw data directory
The raw data coming for the microscope will be automatically copied into the specified `staging` and `longTerm` areas specified in `storageLocations.yaml`. The data will be organized as follows:

- **For NIEHS users**: The directory structure will be `groupName/projecName/YYYYMMDD_sampleName`
- **For NICE users**: The directory structure will be `NICE/groupName/projecName/YYYYMMDD_sampleName`
- **For external collaborations**: The directory structure will be `BorgniaM/collaborations/groupName/projecName/YYYYMMDD_sampleName`

In each directory, you will find a copy of the `session.yaml` and a `raw` directory where the raw `*.tif` or `*.mrc` along with `.mdoc` files will be found.

## Automated emails

Automated emails will be send upon errors and idling in transfers.

- **On errors**: An email will be sent to all addresses in `config/contact_emails.txt`. It will contain the information in `session.yaml` and a traceback of the error to help with troubleshooting.
- **On idle**: If no new files have been found in the source directory for a certain period (45 minutes), an warning email will be sent to all addresses in `config/contact_emails.txt`. This email doesn't mean that something is wrong but may uncover an underlying error in the microscope software or simply inform that all targets were acquired.
- **On completition**: When the session duration has been met, a completion email will be sent to all addresses in `config/contact_emails.txt` as well as all adresses attached in the session's project. It will inform the "owners" of the specimen that their data collection has finished and give them a copy of the microscope parameters, number of images, duration[...] that is saved in `session.yaml`