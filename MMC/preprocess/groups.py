import logging
from MMC import settings
from MMC.lib.groups import Group, ProjectDoesNotExistError, save_groups

from typing import List

logger = logging.getLogger(__name__)

def add_group(name:str, affiliation:str):
    if name in settings.groups:
        logger.info(f'Group {name} already exists')
        return 
    group = Group(name=name,affiliation=affiliation,projects=[])
    logger.info(f'Adding {group}')
    settings.groups[name] = group
    save_groups(settings.groups, settings.groups_file)

def add_projects_to_group(group:str, name:List[str], emails:List[str]):
    if emails is None:
        emails = [] 
    settings.groups[group].add_project(name=name,emailList=emails)
    save_groups(settings.groups, settings.groups_file)

def add_email_to_project(project:str, emails:List[str]):
    group, project = project.split('.')
    project_obj = next((item for item in  settings.groups[group].projects if item.name == project), False)
    if project_obj is False:
        raise ProjectDoesNotExistError()
    [project_obj.add_email(email) for email in emails]
    save_groups(settings.groups, settings.groups_file)
    print(settings.groups[group].print_self())

def display_group_info(name:str='__all__'):

    if name == '__all__':
        for _, group in settings.groups.items():
            print(group.print_self())
        return settings.groups
    print(settings.groups[name].print_self())
    return settings.groups[name]


    



    