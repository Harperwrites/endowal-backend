from app.db.session import SessionLocal
from app.models.deployment import ClientDeployment
from app.core.config import settings

def assert_database_identity(record, config):
    expected=(config.client_id,config.licensee_id,config.license_id,config.parent_license_id)
    actual=(record.client_id,record.licensee_id,record.license_id,record.parent_license_id) if record else None
    if actual != expected:
        raise RuntimeError("Client database identity mismatch. Use this licensee’s dedicated database; do not point a different client at existing data.")

def verify_client_database():
    with SessionLocal() as db:
        assert_database_identity(db.get(ClientDeployment,1),settings)
