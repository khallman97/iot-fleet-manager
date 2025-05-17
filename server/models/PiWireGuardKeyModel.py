from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import INET, BYTEA
from sqlalchemy.ext.declarative import declarative_base
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

Base = declarative_base()

class PiWireGuardKey(Base):
    __tablename__ = "pi_wireguard_keys"

    id = Column(Integer, primary_key=True)
    hostname = Column(String, unique=True, nullable=False)
    wg_ip = Column(INET, nullable=False)                # WireGuard IP assigned to the Pi
    public_key = Column(String, nullable=False)         # WireGuard public key (base64)
    private_key = Column(BYTEA, nullable=False)         # Private key stored as bytes
    server_public_key = Column(String, nullable=False)
    server_endpoint = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class PiWireGuardKeySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PiWireGuardKey
        load_instance = True