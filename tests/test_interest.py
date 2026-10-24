import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import ValidationError
from fastapi import HTTPException
from app.db.base import Base
from app.models import User
from app.models.interest import InterestRequest
from app.routes.interest import InterestInput,save_interest,list_interest
from app.deps import require_roles

class InterestTests(unittest.TestCase):
 def setUp(self):
  self.engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(self.engine);self.db=sessionmaker(bind=self.engine)()
 def tearDown(self):self.db.close();self.engine.dispose()
 def test_contact_is_saved_without_automatic_messages(self):
  result=save_interest(InterestInput(name='Example Partner',email='partner@example.org',audience='donor',note='Discuss support'),self.db)
  self.assertEqual(result,{'status':'saved'});self.assertEqual(self.db.query(InterestRequest).count(),1)
 def test_invalid_or_blank_contact_rejected(self):
  for values in [{'name':' ','email':'a@example.org','audience':'investor'},{'name':'A','email':'bad','audience':'donor'},{'name':'A','email':'a@example.org','audience':'invalid'}]:
   with self.assertRaises(ValidationError):InterestInput(**values)
 def test_contact_list_dependency_requires_admin(self):
  student=User(role='student');teacher=User(role='teacher')
  for user in [student,teacher]:
   with self.assertRaises(HTTPException):require_roles('admin')(user)
  self.assertEqual(list_interest(self.db,User(role='admin')),[])

if __name__=='__main__':unittest.main()
