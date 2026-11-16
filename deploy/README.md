# Launch configuration

**Not a deployed site.** This runs the existing static UI, FastAPI and PostgreSQL behind one origin. Host with HTTPS reverse proxy; no TLS certificates or cloud accounts are included.

1. Copy `.env.release.example` to `.env.release`. Replace all placeholders with secrets and a real HTTPS `PUBLIC_ORIGIN`. Password must be URL-safe because it is placed inside a database URL.
2. `docker compose --env-file .env.release -f compose.release.yml config` to verify interpolation. This can reveal secrets on your screen, so don't share the output.
3. `docker compose --env-file .env.release -f compose.release.yml up --build -d`
4. Put TLS-enabled reverse proxy in front of port 8080 (or use a host that provides HTTPS). Restrict direct access as appropriate.
5. Confirm `https://your-domain/`, `/app/`, `/app/action-atlas/`, `/health`, `/v1/climate-ai/status` and session/preference calls through the browser, including private browsing.
6. Do not share publicly before running the `scripts/preflight.py` checks and reading `RELEASE_NOTES.md`.

The backend auto-runs Alembic migrations in the entrypoint. The database and model volumes are persistent. Models must be trained and copied to the named model volume separately; there is no bundled trained model.

The static web server routes `/v1/` and `/health` to FastAPI, avoiding cross-origin complexity. Local Docker smoke tests require Docker and network access to pull base images.

**Privacy:** Guest sessions do not prove identity; project-interest registrations are consent records only. No social posting or public participation enrollment is enabled.
