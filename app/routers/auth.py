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
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)



def get_user_by_token(token: str):
    print(token)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print(2)
    user_id = payload.get("id")
    print(3)
    username = payload.get("sub")


    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходимо авторизоваться"
        )
    
    user = {"user_id": user_id, "username": username}
    return user


def authenticate_user(db: Annotated[Session, Depends(get_db)], username: str, password: str):
    user = db.scalar(select(User).where(User.login == username))
    if not user or not bcrypt_context.verify(password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def token_refresh_middleware(request: Request, call_next):
    response = await call_next(request)

    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if not access_token or not refresh_token:
        return response

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        remaining = exp_time - datetime.now(timezone.utc)

        # Если до истечения токена меньше 2 минут
        if remaining < timedelta(minutes=Config.TOKEN_MIN_EXEPT):
            username = payload.get("sub")
            user_id = payload.get("id")

            # Создаём новый access токен
            new_token_payload = {
                "sub": username,
                "id": user_id,
                "type": "access",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=Config.MINUTES)
            }
            new_access_token = jwt.encode(new_token_payload, SECRET_KEY, algorithm=ALGORITHM)

            # Обновляем токен в куке
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                secure=False,  # ❗️поменяй на True при HTTPS
                samesite="Lax",
                max_age=Config.MINUTES * 60
            )

    #TODO: Неработает в случае протухшего токена, создать репризеторий на гите и залить
    except:
        try:
            refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if refresh_payload.get("type") != "refresh":
                return JSONResponse({"detail": "Неверный тип refresh токена"}, status_code=401)
            username = refresh_payload.get("sub")
            user_id = refresh_payload.get("id")
            # Генерируем новый access токен
            new_token_payload = {
                "sub": username,
                "id": user_id,
                "type": "access",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=Config.MINUTES)
            }
            new_access_token = jwt.encode(new_token_payload, SECRET_KEY, algorithm=ALGORITHM)
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=Config.MINUTES * 60
            )
            print(4)

        except jwt.PyJWTError:
            return JSONResponse({"detail": "Refresh токен недействителен"}, status_code=401)

    return response


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
        print("Ошибка регистрации:", e)  # <-- чтобы понять, если снова что-то не так
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