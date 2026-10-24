# Client branding and licensed deployments

Endowal uses **one API deployment and one dedicated database per client**. This is
not a shared-database tenant router. A school/program can use the same source
release with its own frontend, API URL, database, signing secret, and branding.
The same email can belong to separate accounts in different deployments.

## Branding (frontend repository)

1. Copy `config/clients/example-school.json` to `<client-id>.json`.
2. Put the client's logo under `public/clients/<client-id>/`.
3. Register the JSON in `lib/client-config.ts`'s `profiles` map.
4. Set `NEXT_PUBLIC_CLIENT_ID=<client-id>` and
   `NEXT_PUBLIC_API_BASE_URL=<that client's API origin>` in deployment variables.
5. Restart development or rebuild the frontend. Client selection is build-time.

Profiles contain the display name, tagline, description, local logo path, bank
name, navigation/role labels, three theme colors, registration setting, and
feature switches for credit, check writing, messaging, the public demo, and
interest collection. Shared pastel illustration palettes remain consistent;
client theme colors override primary actions, public page paper, and accents.
Curriculum, legal notices, and marketing copy live in the relevant components
and should be reviewed for each client; this is not a blanket text-replacement
system. Feature switches are deployment configuration, not paid entitlements.

The example profile uses placeholder branding, not a real school's identity.
Default Endowal browser keys are preserved. Other clients use separate token,
remembered-email, dashboard-preference, and lesson-progress namespaces.

## API and database configuration

Copy `.env.example` to `.env` in this backend's own deployment. Example local
school configuration (use a separate checkout/environment from Endowal):

```dotenv
CLIENT_ID=example-school
LICENSEE_ID=example-school
LICENSE_ID=school-license-001
PARENT_LICENSE_ID=partner-license-001
DEPLOYMENT_ENVIRONMENT=development
DATABASE_URL=sqlite:///./example-school.db
SECRET_KEY=<generate-a-unique-random-secret-for-this-client>
CORS_ORIGINS=["http://127.0.0.1:3001"]
ALLOW_SELF_REGISTRATION=false
CREDIT_ENABLED=true
MESSAGING_ENABLED=true
INTEREST_ENABLED=false
```

Pair it with frontend `NEXT_PUBLIC_CLIENT_ID=example-school` and API URL
`http://127.0.0.1:8001`. Start that frontend on port 3001 and API on port 8001.
The frontend/API ID, registration setting and server-backed feature flags must
match; authenticated pages block when they do not. Optional features are also
blocked by API middleware. UI visibility alone does not grant/revoke user roles.

Apply migrations **with that client's environment already configured**:

```bash
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m scripts.create_client_admin
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

The administrator bootstrap prompts for the new password without writing it to
arguments or files. Administrators can provision accounts using the existing
admin-only user endpoints. Public registration can be disabled for schools.
Default demo seed scripts refuse to run outside Endowal development mode.

Migration `0010_client_deployment` pins the database to client/license metadata.
At startup the API rejects a configuration that disagrees with that record.
Never reuse another client's database or copy real student data into a new
client. Changing an existing license relationship requires an intentional,
audited update of deployment metadata; changing env vars alone fails closed.
JWT access tokens are bound to `CLIENT_ID` via their audience. Remembered-session
cookies and browser keys are client-specific. The default Endowal cookie keeps
its old name so existing users can renew without retyping credentials.

## License / sublicense metadata

- `CLIENT_ID`: deployment identity, e.g. `example-school`.
- `LICENSEE_ID`: organization using this deployment.
- `LICENSE_ID`: identifier for its license record.
- `PARENT_LICENSE_ID`: optional parent agreement/license for sublicensing.

These fields are bookkeeping and isolation safeguards. They do **not** create
contracts, verify licensing rights, collect royalties, meter seats, or enforce
expiration. Central license issuance, billing, reseller management, shared SSO,
and a shared-database multi-tenant control plane are separate future features.
No parent license automatically receives access to student data.

## Production checklist for each deployment

Use a dedicated database and backups, separate HTTPS frontend/API origins, a
unique random `SECRET_KEY` (32+ characters), a non-development `LICENSE_ID`,
explicit HTTPS `CORS_ORIGINS`, and `DEPLOYMENT_ENVIRONMENT=production`. Runtime
settings reject the development signing secret/license and non-HTTPS CORS in
production. Keep all secrets server-side. Configure access, support, retention,
and deployment operations for the client before onboarding real users.
