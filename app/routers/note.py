from random import randint

from fastapi import APIRouter
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, status, HTTPException, Request, Query, Cookie, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func, delete

import jwt
from loguru import logger

from app.models import *
from app.routers import auth
from app.database import get_db
from app.schemas import *

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')

router = APIRouter()

@router.post('/')
async def create_note(
    db: Annotated[Session, Depends(get_db)],
    note_data: NoteBase,
    token: str = Depends(auth.get_token_from_cookie)
):
    try:
        if not auth.get_user_by_token(token=token):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"   
            )

        note = Note(
            owner_id=auth.get_user_by_token(token=token)["user_id"],
            folder_id=note_data.folder_id,
            slug=f"note_{randint(1, 1000)}",
            text=note_data.text,
            name=note_data.name,
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        return note
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



@router.get('/all/')
async def get_all_notes(
    db: Annotated[Session, Depends(get_db)],
):
    try:
        query = select(Note)
        result = db.execute(query)

        return result.scalars().all()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
        )


@router.get('/{note_id}/')
async def get_note_by_id(
    note_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        query = select(Note).where(Note.id == note_id)
        result = db.execute(query)

        return result.scalars().one()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
        )


@router.get('/by_user/{user_id}/')
async def get_note_by_user_id(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        query = select(Note).where(Note.owner_id == user_id)
        result = db.execute(query)

        return result.scalars().all()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
        )

@router.delete('/mass_deleting/')
async def del_notes_by_id(
    notes_id: List[int],
    db: Annotated[Session, Depends(get_db)]
):

    try:
        if not notes_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Нет объектов для удаления"
            )

        db.execute(delete(Note).where(Note.id.in_(notes_id)))
        db.commit()

        return "OK"

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete('/{note_id}/')
async def del_note_by_id(
    note_id: int,
    db: Annotated[Session, Depends(get_db)]
):

    try:
        obj_del = db.scalar(select(Note).where(Note.id == note_id))
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


@router.put('/{note_id}/')
async def update_note(
        note_id: int,
        note_data: NoteBase,
        db: Annotated[Session, Depends(get_db)]
):
    try:
        db_note = db.scalar(select(Note).where(Note.id == note_id))
        if not db_note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объект не найден"
            )

        for field, value in note_data.dict(exclude_unset=True).items():
            setattr(db_note, field, value)

        db.add(db_note)
        db.commit()
        db.refresh(db_note)

        return {"message": "UPDATE OK", "note": db_note}

    except Exception as e:
        db.rollback()  # Откатываем изменения в случае ошибки
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get('/by_folder/{folder_id}/')
async def get_notes_by_folder_id(
    folder_id: int,
    db: Annotated[Session, Depends(get_db)],
    token: str = Depends(oauth2_scheme),
):
    try:
        user = auth.get_user_by_token(token=token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"   
            )
        
        query = select(Note).where(Note.owner_id == user["user_id"]).where(Note.folder_id == folder_id)
        result = db.execute(query)

        return result.scalars().all()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
        )

@router.patch('/{note_id}/')
async def move_one_note(
        note_id: int,
        folder_id: int,
        db: Annotated[Session, Depends(get_db)]
):
    try:
        db_note = db.scalar(select(Note).where(Note.id == note_id))
        if not db_note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объект не найден"
            )

        db_note.folder_id = folder_id


        db.commit()
        db.refresh(db_note)

        return {"message": "UPDATE OK", "note": db_note}

    except Exception as e:
        db.rollback()  # Откатываем изменения в случае ошибки
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/mass_move/")
async def move_notes(
    payload: MoveNotesRequest=Body(...),
    db: Session = Depends(get_db)
):
    try:
        notes = db.scalars(select(Note).where(Note.id.in_(payload.note_ids))).all()

        if len(notes) != len(payload.note_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Одна или несколько заметок не найдены"
            )

        for note in notes:
            note.folder_id = payload.folder_id

        db.commit()

        return {"message": "UPDATE OK"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )