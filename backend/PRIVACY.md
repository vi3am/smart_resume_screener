# Resume data privacy policy

Resumes and extracted candidate details are personal data. Use only material
provided with permission and anonymize it before using it as demo or evaluation
data.

## Access and upload controls

- Resume endpoints require authentication and verify that the recruiter owns
  the parent job.
- Uploads are limited to 5 MiB and accepted only when the filename extension,
  declared MIME type, and PDF or DOCX structure agree.
- The original filename is kept only as a display value; it is never used as a
  storage path. Stored files use random names in a directory with owner-only
  permissions and are not executed.
- The uploaded document is deleted immediately after parsing. Only the
  extracted text, parsed details, and scores are retained in the database.

## Retention and deletion

Resume records, extracted text, parsed details, and associated scores are kept
for at most `RESUME_RETENTION_DAYS` days (default: 180), unless the recruiter
deletes the resume earlier. Configure a daily scheduled task to run this command
from `backend/`:

```sh
.venv/bin/python -m app.cleanup_expired_resumes
```

Example daily cron entry (replace the path with the absolute backend directory):

```cron
0 3 * * * cd /path/to/smart-resume-screener/backend && .venv/bin/python -m app.cleanup_expired_resumes
```

The authenticated owner can also delete a resume immediately using
`DELETE /jobs/{job_id}/resumes/{resume_id}`. This removes its extracted text,
parsed data, legacy score, and per-run score rows. The cleanup command also
removes stale files created by the upload flow.

## Operational requirements

- Keep application and database secrets in ignored local environment files or
  a deployment secret manager; never use the seed script's demo account with a
  shared or production database.
- Schedule the cleanup task and verify its logs as part of deployment. The
  application does not create an operating-system scheduler automatically.
- Backups may retain deleted data according to the backup system's separate
  expiry policy; production deployments must define that policy too.
