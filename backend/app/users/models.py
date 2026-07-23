from sqlalchemy import Boolean, Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# Association tables for many-to-many relationships (public schema)
user_driver_follows = Table(
    'user_driver_follows',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('driver_id', String, ForeignKey('f1.drivers.driver_id'), primary_key=True)
)

user_constructor_follows = Table(
    'user_constructor_follows',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('constructor_id', String, ForeignKey('f1.constructors.constructor_id'), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    is_superuser = Column(Boolean, nullable=False, default=False, server_default="false")
    is_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    followed_drivers = relationship("Driver", secondary=user_driver_follows, backref="followers")
    followed_constructors = relationship("Constructor", secondary=user_constructor_follows, backref="followers")
