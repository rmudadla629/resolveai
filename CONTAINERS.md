# Local container setup

## Verification status

The GitHub Actions container job has passed image build, in-image regression tests, Compose syntax validation, and HTTP startup checks. Docker was unavailable locally when packaging was prepared; these CI results do not establish a local Mac container run. Full Compose model inference and Apple Silicon execution still require a local run; CI does not download Ollama or models.

## Prerequisites

Install Docker Desktop for Apple Silicon from Docker's official site and start it. Verify `docker version` and `docker compose version` in Terminal. Allow disk space for a Linux VM, images, and a separate model download. The native Ollama downloads are not reused. Docker's Linux VM runs Ollama on CPU in this setup, so responses can be slower than the native Mac app; the existing native setup remains available.

## Start and configure

From the repository directory:

```sh
docker compose build
docker compose up -d
docker compose exec ollama ollama pull qwen3:4b
docker compose exec ollama ollama pull all-minilm:22m
docker compose exec app python -m resolveai.auth
docker compose exec app python -m resolveai.customers
docker compose exec app python -m resolveai.customers
docker compose exec app python -m resolveai.doctor
```

Create the reviewer and the fictional customers Alex and Sam using private passwords. Container accounts start fresh: native host credentials are not copied into the image. Do not rerun account creation if already configured in the volume. Wait for Ollama startup before pulling models; retry the command if it initially reports connection refused.

Open http://127.0.0.1:8001/. Native ResolveAI can continue on port 8000. Follow the account, ownership, policy, and review steps in DEMO.md using port 8001. Compose publishes the app only on localhost, and does not publish the Ollama API. Model traffic uses the private service hostname `ollama`.

```sh
docker compose ps
docker compose logs --tail=50 app
docker compose exec app python -m resolveai.evaluate
docker compose exec app python -m resolveai.compare_retrieval
```

The image health check tests the HTTP application, not model availability or credential configuration. Doctor checks those prerequisites separately. Slow CPU inference may hit the current model timeout; do not claim full inference validation until you run it successfully.

## Persistence and stop

```sh
docker compose down
```

Named volumes preserve accounts, review state, traces, reports, and models across container recreation. Do not add `--volumes` unless you intend to delete that state. Docker Desktop's volume export can preserve reports or backups. Container and native demo state are independent.

For a confirmed demo reset, stop the app first, then run the preview and reset in a one-off container using the same volume:

```sh
docker compose stop app
docker compose run --rm --no-deps app python -m resolveai.demo
docker compose run --rm --no-deps app python -m resolveai.demo --server-stopped --confirm RESET-DEMO
docker compose up -d app
```

The reset preserves credentials and creates database backups in the demo-state volume. It does not reset the native app's data.

## Configuration and limits

`RESOLVEAI_OLLAMA_URL` sets an operator-controlled HTTP(S) origin with no path or credentials. The native default is http://127.0.0.1:11434; Compose sets http://ollama:11434. It is not controlled by web users. The app image runs as UID 10001, drops Linux capabilities in Compose, uses a read-only root filesystem, and writes only to runtime/report volumes and temporary storage.

Dependency versions and the Ollama release are pinned, but image tags are not digest-locked. This improves setup consistency without establishing bit-for-bit reproducibility. Keep a single app instance: sessions, CSRF tokens, and login limits are process-local. HTTPS, Secure cookies, shared session/rate-limit storage, and public deployment validation remain unfinished. No registry publication or hosting is configured.
