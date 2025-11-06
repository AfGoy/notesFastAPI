from datetime import datetime
from typing import Annotated, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette import status
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.requests import Request
import httpx

from app.config import Config
from app.database import get_db
from app.routers import note, auth, folders
from app.routers.auth import oauth2_scheme, auto_refresh_token

from fastapi.templating import Jinja2Templates

load_dotenv()


app = FastAPI(
    title="FastAPI notes",
    description="API",
    version="0.0.1"
)

app.middleware("http")(auto_refresh_token)

templates = Jinja2Templates(directory='app/templates/')

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(note.router, prefix="/note", tags=["note"])
app.include_router(folders.router, prefix="/folder", tags=["folder"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/", response_class=HTMLResponse)
async def main(
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
      
        async with httpx.AsyncClient() as client:
            response_folders = await client.get(f"{Config.URL}/folder/by_user/{user['user_id']}/")
            response_notes = await client.get(f"{Config.URL}/note/by_user/{user['user_id']}/")
            response_folders.raise_for_status()
            response_notes.raise_for_status()
            folders = response_folders.json()
            notes = response_notes.json()

        for folder in folders:
            dt = datetime.fromisoformat(folder["updated_at"])
            folder["updated_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")

        
        for note in notes:
            dt = datetime.fromisoformat(note["updated_at"])
            note["updated_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")

        
        return templates.TemplateResponse(
            "main.html",
            {
                "request": request,
                "config": {"url": Config.URL},
                "username": user["username"],
                "notes": notes,
                "folders": folders
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