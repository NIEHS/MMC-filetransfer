from pathlib import Path
from datetime import datetime, timedelta

from typing import List
import logging

from fastapi import FastAPI, Request, status, Response, BackgroundTasks, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm

from MMC import settings

import auth
import groups
import sessions

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(groups.groups)
app.include_router(sessions.sessions)
app.add_exception_handler(auth.NotAuthenticatedException,auth.not_authenticated_exception_handler)

templates = Jinja2Templates(directory="templates")
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://mri20-dtn01:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse,)
async def home(request: Request, current_user: auth.User = Depends(auth.get_current_active_user)):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get('/scopes/', response_model=List[str])
async def list_scopes() -> List[str]:
    return list(settings.scopes.keys())

@app.get('/path/')
async def list_path(value:str):
    path = Path(value)
    root = Path(path.parent)
    remainder = path.name + '*'
    if root.exists:
        return root.glob(remainder)


@app.post("/token", response_model=auth.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth.authenticate_user(auth.fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=auth.User)
async def read_users_me(current_user: auth.User = Depends(auth.get_current_active_user)):
    return current_user

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post('/login')
async def login_submit(form_data: auth.OAuth2PasswordRequestFormData):
    logger.debug(form_data)
    token = await login_for_access_token(form_data)
    logger.debug(token)
    # header= {
    #     "Authorization": f"{token['token_type']} {token['access_token']}",
    # }
    # response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    # response = Response()
    # response.set_cookie(
    #         "Authorization",
    #         value=f"Bearer {token['access_token']}",
    #         domain="mri20-dtn01",
    #         httponly=True,
    #         max_age=1800,
    #         expires=1800,
    #     )
    return f"Bearer {token['access_token']}"



    