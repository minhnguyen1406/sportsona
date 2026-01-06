from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# Association tables for many-to-many relationships
user_driver_follows = Table(
    'user_driver_follows',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('driver_id', String, ForeignKey('drivers.driver_id'), primary_key=True)
)

user_constructor_follows = Table(
    'user_constructor_follows',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('constructor_id', String, ForeignKey('constructors.constructor_id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    followed_drivers = relationship("Driver", secondary=user_driver_follows, back_populates="followers")
    followed_constructors = relationship("Constructor", secondary=user_constructor_follows, back_populates="followers")
