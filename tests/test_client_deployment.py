import asyncio
import unittest
from types import SimpleNamespace
from datetime import timedelta
from jose import jwt,JWTError
from starlette.requests import Request
from starlette.responses import Response
from pydantic import ValidationError
from app.core.config import Settings,settings
from app.core.deployment import assert_database_identity
from app.core.security import create_access_token
from app.main import client_features

class ClientDeploymentTests(unittest.TestCase):
 def test_database_cannot_be_reused_for_other_client_or_license(self):
  config=SimpleNamespace(client_id='school-a',licensee_id='school-a',license_id='license-a',parent_license_id='partner-1')
  record=SimpleNamespace(**vars(config));assert_database_identity(record,config)
  for key in ['client_id','licensee_id','license_id','parent_license_id']:
   other=SimpleNamespace(**{**vars(record),key:'different'})
   with self.assertRaises(RuntimeError):assert_database_identity(other,config)
  with self.assertRaises(RuntimeError):assert_database_identity(None,config)
 def test_tokens_are_bound_to_deployment_audience(self):
  token=create_access_token({'sub':'1','role':'student'},timedelta(minutes=1))
  self.assertEqual(jwt.decode(token,settings.secret_key,algorithms=[settings.algorithm],audience=settings.client_id)['aud'],settings.client_id)
  with self.assertRaises(JWTError):jwt.decode(token,settings.secret_key,algorithms=[settings.algorithm],audience='different-school')
 def test_production_requires_secret_license_and_https_origins(self):
  with self.assertRaises(ValidationError):Settings(_env_file=None,deployment_environment='production')
  config=Settings(_env_file=None,deployment_environment='production',secret_key='a'*40,license_id='licensed-123',cors_origins=['https://school.example.org'])
  self.assertEqual(config.license_id,'licensed-123')
 def test_client_id_is_safe_for_namespacing(self):
  with self.assertRaises(ValidationError):Settings(_env_file=None,client_id='../another client')
 def test_mismatched_client_header_rejected_before_route(self):
  request=Request({'type':'http','method':'GET','path':'/wallets','headers':[(b'x-endowal-client',b'other-school')]})
  called=[]
  async def next_handler(req):called.append(True);return Response(status_code=200)
  response=asyncio.run(client_features(request,next_handler));self.assertEqual(response.status_code,409);self.assertEqual(called,[])

if __name__=='__main__':unittest.main()
