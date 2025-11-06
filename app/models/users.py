from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String)
    hash_password = Column(String)

    notes = relationship('Note', back_populates='owner')
    folders = relationship('Folder', back_populates='owner')