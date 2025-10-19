from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from datetime import datetime

class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    slug = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    name = Column(String)
    updated_at = Column(DateTime, default=lambda: datetime.utcnow())
    color = Column(String(20))
    is_public = Column(Boolean, default=False)
    password_check = Column(Boolean, default=False)
    hash_password = Column(String)

    owner = relationship('User', back_populates='folders')
    notes = relationship('Note', back_populates='folder')