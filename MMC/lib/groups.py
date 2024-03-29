import logging
from pydantic import BaseModel, Field
from typing import List, Optional
import yaml
from collections import OrderedDict

logger = logging.getLogger(__name__)

class ProjectDoesNotExistError(Exception):
    pass

class GroupDoesNotExistError(Exception):
    pass

class Project(BaseModel):
    name: str
    emailList: List[str] = Field(default_factory=list, alias='emails')

    class Config:
        allow_population_by_field_name = True

    def add_email(self,email):
        if email in self.emailList:
            logger.info(f'{email} already in {self.name} project, skipping')
            return
        self.emailList.append(email)

    
    def print_self(self):
        return f"{self.name}: {', '.join(self.emailList)}"


class Group(BaseModel):
    name: str
    affiliation: str
    projects: List[Project] = Field(default_factory=list)

    def add_project(self, name:str, emailList:List[str]):
        if name in list(map(lambda x : x.name, self.projects)):
            logger.info(f'Project {name} already exists for group {self.name}')
            return
        logger.info(f'Adding project {name} to group {self.name}')
        self.projects.append(Project(name=name, emailList=emailList)) 
    
    def print_self(self):
        string = ""
        for p in self.projects:
            string += f"\n{' ':5}{p.print_self()}"
        return f"""{'#'*60}\n{'Group:':<15} {self.name}\n{'Affiliation:':<15} {self.affiliation}\n{'Pojects:':}{string}\n{'#'*60}"""

def load_groups(groups_file) -> dict:
    output_groups= {}
    if not groups_file.exists():
        return output_groups
    with open(groups_file) as f:
        groups = yaml.safe_load(f)
    if groups is None:
        return output_groups
    for group in groups:
        group = Group.parse_obj(group)
        output_groups[group.name] = group
    return OrderedDict(sorted(output_groups.items()))

def save_groups(groups, groups_file):
    export_groups = []
    for _, group in groups.items():
        export_groups.append(group.dict())
    with open(groups_file, 'w') as f:
        f.write(yaml.dump(export_groups))
    return groups



