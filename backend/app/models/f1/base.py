from sqlalchemy import Column, String, Integer, Date, Time, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

# All F1 tables live in 'f1' schema
SCHEMA = "f1"
