from sqlalchemy import Integer,String
from sqlalchemy.orm import Mapped,mapped_column
from app.db.base import Base
class ClientDeployment(Base):
    __tablename__="client_deployment"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    client_id:Mapped[str]=mapped_column(String(80),nullable=False)
    licensee_id:Mapped[str]=mapped_column(String(120),nullable=False)
    license_id:Mapped[str]=mapped_column(String(120),nullable=False)
    parent_license_id:Mapped[str|None]=mapped_column(String(120))
