import logging
from pathlib import Path

from fastapi import Request, status, Response, Depends, APIRouter
from fastapi.responses import HTMLResponse 
from fastapi.templating import Jinja2Templates

from MMC.lib.groups import Group, save_groups
from MMC import settings
from MMC.restAPI import auth

logger = logging.getLogger(__name__)

groups= APIRouter(dependencies=[Depends(auth.get_current_active_user)])

templates = Jinja2Templates(directory=Path(__file__).parent / "templates" / "groups")

@groups.get('/groups/affiliations/')
async def list_affiliations():
    return settings.affiliations

@groups.get('/groups/view/list/', response_class=HTMLResponse)
async def display_group_info(request: Request):
    return templates.TemplateResponse("groups.html", {"request": request,"groups": settings.groups})

@groups.get('/groups/list/')
async def display_group_info():
    return settings.groups

@groups.post('/groups/add', status_code=status.HTTP_201_CREATED, )
async def add_group(group:Group,response:Response):
    if group.name in settings.groups:
        logger.info(f'Group {group.name} already exists')
        response.status_code = status.HTTP_208_ALREADY_REPORTED
        return settings.groups[group.name]
    settings.groups[group.name] = group
    save_groups(settings.groups, settings.groups_file)
    return settings.groups

@groups.patch('/groups/update')
async def update_group(group:Group,response:Response):
    settings.groups[group.name] = group
    groups = save_groups(settings.groups, settings.groups_file)
    logger.info(f'Updated group {group}')
    logger.info(f'{groups}')
    return groups