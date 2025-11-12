from __future__ import annotations

from sqlalchemy import Column, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base


Base = declarative_base()


###############################################################################
class RouletteSeries(Base):
    __tablename__ = "ROULETTE_SERIES"
    id = Column(Integer, primary_key=True)
    extraction = Column(Integer)
    color = Column(String)
    color_code = Column(Integer)
    position = Column(Integer)
    __table_args__ = (UniqueConstraint("id"),)


###############################################################################
class PredictedGames(Base):
    __tablename__ = "PREDICTED_GAMES"
    id = Column(Integer, primary_key=True)
    checkpoint = Column(String)
    extraction = Column(Integer)
    predicted_action = Column(String)
    __table_args__ = (UniqueConstraint("id"),)
