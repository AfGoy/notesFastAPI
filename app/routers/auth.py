from datetime import timedelta, datetime, timezone
from typing import Annotated

from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status, Cookie, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import select, update, insert

from passlib.context import CryptContext

import jwt
from jose import jwt, JWTError

from app.database import get_db
from app.config import Config
from app.models import User


templates = Jinja2Templates(directory='app/templates/')

SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')


def get_token_from_cookie(
    token: str = Cookie(alias="access_token", default=None)
) -> str:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен отсутствует в куках"
        )
    return token


def create_access_token(username: str, user_id: int,
                              expires_delta: timedelta):
    payload = {
        'sub': username,
        'id': user_id,
        'exp': datetime.now(timezone.utc) + expires_delta
    }

    payload['exp'] = int(payload['exp'].timestamp())
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(username: str, user_id: int, expires_delta: timedelta):
    payload = {
        "sub": username,
        "id": user_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + expires_delta 
    }
    payload['exp'] = int(payload['exp'].timestamp())
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)



def get_user_by_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        username = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Необходимо авторизоваться"
            )
        
        user = {"user_id": user_id, "username": username}
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен"
        )


def authenticate_user(db: Annotated[Session, Depends(get_db)], username: str, password: str):
    user = db.scalar(select(User).where(User.login == username))
    if not user or not bcrypt_context.verify(password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def set_token(request: Request,
                    token: str,
                    secret_key: str,
                    call_next):
    payload = jwt.decode(
        token,
        secret_key,
        algorithms=[Config.ALGORITHM]
    )

    new_access_token = create_access_token(
        username=payload["sub"],
        user_id=payload["id"],  
        expires_delta=timedelta(minutes=Config.MINUTES)
    )

    response = await call_next(request)

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        max_age=Config.MINUTES * 60,
        secure=True,
        samesite='lax',
        path='/'
    )
    return response


async def auto_refresh_token(request: Request, call_next):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if request.url.path.startswith("/auth/"):
        return await call_next(request)

    if not access_token or not refresh_token:
        return await call_next(request)

    try:
        payload = jwt.decode(access_token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        exp = payload.get("exp")
        if exp is None:
            raise JWTError("No exp in access token")

        now = datetime.now(timezone.utc)
        token_expire_time = datetime.fromtimestamp(exp, tz=timezone.utc)
        time_until_expire = token_expire_time - now

        if timedelta(seconds=20) < time_until_expire < timedelta(minutes=Config.TOKEN_MIN_EXEPT):
            return await set_token(
                request=request,
                token=access_token,
                secret_key=Config.SECRET_KEY,
                call_next=call_next
            )
        else:
            return await call_next(request)

    except jwt.ExpiredSignatureError:
        try:
            refresh_payload = jwt.decode(
                refresh_token,
                Config.SECRET_KEY,
                algorithms=[Config.ALGORITHM]
            )
            if refresh_payload.get("type") != "refresh":
                raise JWTError("Invalid refresh token type")

            return await set_token(
                request=request,
                token=access_token,
                secret_key=Config.SECRET_KEY,
                call_next=call_next
            )

        except JWTError:
            pass

    except JWTError:
        pass

    return await call_next(request)


def create_and_save_tokens(user, response: Response):
    access_token = create_access_token(
        user.login, user.id, expires_delta=timedelta(minutes=Config.MINUTES)
    )
    refresh_token = create_refresh_token(
        user.login, user.id, expires_delta=timedelta(days=Config.REFRESH_TOKEN_DAYS)
    )


    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="Lax",
        max_age=Config.MINUTES * 60
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="Lax",
        max_age=Config.REFRESH_TOKEN_DAYS * 24 * 60 * 60
    )

router = APIRouter()

@router.post("/token")
async def login(
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = authenticate_user(db, form_data.username, form_data.password)
    create_and_save_tokens(user, response)


    return {"message": "OK"}
    

@router.post("/register")
async def register(
    response: Response,
    db: Session = Depends(get_db),
    login: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return JSONResponse(
            content={"detail": "Пароли не совпадают"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        existing_user = db.scalar(select(User).where(User.login == login))
        if existing_user:
            return JSONResponse(
                content={"detail": "Пользователь с таким логином уже существует"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = User(login=login, hash_password=bcrypt_context.hash(password))
        db.add(user)
        db.commit()
        db.refresh(user)

        create_and_save_tokens(user, response), 
        return {"message": "OK"} 
    
        #TODO:
        #Переадрисовавывать на главную страницу

    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"detail": "Ошибка регистрации"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
        

    
@router.get("/create", response_class=HTMLResponse)
def create_auth_form(request: Request):
    return templates.TemplateResponse(
        "auth/create_auth_form.html",
        {
            "request": request,
            "config": {"url": Config.URL}
        }
    )