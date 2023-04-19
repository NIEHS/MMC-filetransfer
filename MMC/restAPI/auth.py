from typing import Optional
import base64
import json
# from passlib.context import CryptContext
from datetime import datetime, timedelta
import logging

import jwt
from jwt import PyJWTError

from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi.param_functions import Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


logger = logging.getLogger(__name__)


templates = Jinja2Templates(directory="templates")
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "password": "admin",
        "disabled": False,
    }
}
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = 'cbkdjb7yrt8743goqifgb433jhb11092e3wkwhbfdj'
ALGORITHM = "HS256"


from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from passlib.context import CryptContext
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    password: str


# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class MyOAuth2PasswordBearer(OAuth2PasswordBearer):

    async def __call__(self, request: Request) -> Optional[str]:
        logger.debug(request.headers)
        # logger.debug(request.__dict__)
        # async def __call__(self, request: Request) -> Optional[str]:

        authorization: str = request.cookies.get("Authorization")
        logger.debug(authorization)
        scheme, param = get_authorization_scheme_param(authorization.replace('%20', ' '))
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        logger.debug(param)
        return param
    
class OAuth2PasswordRequestFormData(BaseModel):
    username: str
    password:str


oauth2_scheme = MyOAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

# app = FastAPI()


# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)


# def get_password_hash(password):
#     return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    logger.debug(user)
    if not user:
        return False
    if password != user.password:
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class NotAuthenticatedException(Exception):
    def __init__(self, name: str):
        self.name = name


async def not_authenticated_exception_handler(request: Request, exc: NotAuthenticatedException):
    return RedirectResponse('/login')


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # credentials_exception = NotAuthenticatedException(name='Not Authenticated')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user




