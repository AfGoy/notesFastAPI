from pydantic import BaseModel
from typing import Optional
    

class NoteBase(BaseModel):
    name: str
    text: Optional[str] = None
    folder_id: Optional[int] = None
    is_public: bool = False



class FolderCreate(BaseModel):
    name: str
    color: str
    is_public: bool = False
    password_check: bool = False
    password: Optional[str] = None