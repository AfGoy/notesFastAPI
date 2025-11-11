from random import randint

from fastapi import APIRouter
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, status, HTTPException, Request, Query, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func
from starlette.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json

import jwt
from loguru import logger

from app.models import *
from app.routers import auth
from app.database import get_db
from app.schemas import *
from app.config import Config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')
templates = Jinja2Templates(directory='app/templates/')

router = APIRouter()

@router.post('/')
async def create_folder(
    db: Annotated[Session, Depends(get_db)],
    folder_data: FolderCreate,  
    token: str = Depends(auth.get_token_from_cookie)
):
    try:
        user = auth.get_user_by_token(token=token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        folder = Folder(
            owner_id=user["user_id"],
            slug = f"folder_{randint(0, 10000)}",
            color=folder_data.color,
            name=folder_data.name,
            is_public=folder_data.is_public,
            password_check=folder_data.password_check,
            hash_password=folder_data.password,
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)

        return folder

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get('/{folder_id}/')
async def get_folder_by_id(
    folder_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        query = select(Folder).where(Folder.id == folder_id)
        result = db.execute(query)

        return result.scalars().one()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
        )


@router.get('/by_user/{user_id}/')
async def get_folders_by_user_id(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        query = select(Folder).where(Folder.owner_id == user_id)
        result = db.execute(query)

        return result.scalars().all()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
        )

@router.delete('/{folder_id}/')
async def del_folder_by_id(
    folder_id: int,
    db: Annotated[Session, Depends(get_db)]
):

    try:
        obj_del = db.scalar(select(Folder).where(Folder.id == folder_id))
        if not obj_del:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Объект не найден"
            )

        db.delete(obj_del)
        db.commit()

        return "OK"

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put('/{folder_id}/')
async def update_folder(
        folder_id: int,
        folder_data: FolderCreate,
        db: Annotated[Session, Depends(get_db)]
):
    try:
        db_folder = db.scalar(select(Folder).where(Folder.id == folder_id))
        if not db_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объект не найден"
            )

        for field, value in folder_data.dict(exclude_unset=True).items():
            setattr(db_folder, field, value)

        db.add(db_folder)
        db.commit()
        db.refresh(db_folder)

        return {"message": "UPDATE OK", "folder": db_folder}

    except Exception as e:
        db.rollback()  # Откатываем изменения в случае ошибки
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/folder_page/{folder_id}", response_class=HTMLResponse)
async def folder_page(
        folder_id: int,
        request: Request,
        db: Annotated[Session, Depends(get_db)],
        token: Optional[str] = None

):
    try:
        if not token:
            token = request.cookies.get("access_token")

        if not token:
            return RedirectResponse(url="/auth/create", status_code=status.HTTP_303_SEE_OTHER)

        user = auth.get_user_by_token(token=token)
        if not user:
            return RedirectResponse(url="/auth/create", status_code=status.HTTP_303_SEE_OTHER)
        
        folder = None
        notes = []
        async with httpx.AsyncClient() as client:
            response_folder = await client.get(f"{Config.URL}/folder/{folder_id}/")
            folder = response_folder.json()

        query = select(Note).where(Note.owner_id == user["user_id"]).where(Note.folder_id == folder_id)
        result = db.execute(query)

        notes = result.scalars().all()

        return templates.TemplateResponse(
            "folder.html",
            {
                "request": request,
                "config": {"url": Config.URL},
                "username": user["username"],
                "user_id": user["user_id"],
                "folder": folder,
                "notes": notes
            }

        )

    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse(url="/auth/create", status_code=status.HTTP_303_SEE_OTHER)
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка на сервере"
        )

