"""Bootstrap a dedicated deployment's administrator without storing a password in files."""
from getpass import getpass
from pydantic import TypeAdapter,EmailStr
from app.core.deployment import verify_client_database
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models import User

def main():
    verify_client_database()
    email=str(TypeAdapter(EmailStr).validate_python(input('Administrator email: ').strip()))
    name=input('Administrator display name: ').strip()
    password=getpass('New password (12+ characters): ')
    if len(password)<12 or password!=getpass('Confirm password: '):raise ValueError('Passwords must match and contain at least 12 characters')
    with SessionLocal() as db:
        if db.query(User).filter_by(email=email).first():raise ValueError('This account already exists; no changes made')
        db.add(User(email=email,name=name or 'Administrator',role='admin',is_active=True,password_hash=get_password_hash(password)))
        db.commit()
    print('Administrator created. Use the client sign-in page to continue.')
if __name__=='__main__':main()
