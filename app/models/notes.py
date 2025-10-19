from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from datetime import datetime

from app.database import Base



class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    folder_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    slug = Column(String, unique=True, nullable=False)
    text = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    name = Column(String)
    updated_at = Column(DateTime, default=lambda: datetime.utcnow())
    is_public = Column(Boolean, default=False)

    owner = relationship('User', back_populates='notes')
    folder = relationship('Folder', back_populates='notes')