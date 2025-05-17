from sqlalchemy import Column, String, Float, TIMESTAMP
from sqlalchemy.dialects.postgresql import TIMESTAMP as PG_TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PiMetric(Base):
    __tablename__ = "pi_metrics"

    time = Column(PG_TIMESTAMP(timezone=True), primary_key=True)
    hostname = Column(String, primary_key=True)
    cpu_percent = Column(Float)
    memory_used = Column(Float)
    memory_total = Column(Float)
    disk_used = Column(Float)
    disk_total = Column(Float)
    uptime = Column(Float)