set shell := ["bash", "-euo", "pipefail", "-c"]

# Lists the commands.
default:
    @just --list

# Prepares frozen source tools without application installation or lifecycle scripts.
setup-source:
    cmp --silent .bun-version <(bun --version)
    cd frontend && bun install --frozen-lockfile --ignore-scripts
    cd tools/api-client && bun install --frozen-lockfile --ignore-scripts
    cd backend && UV_PROJECT_ENVIRONMENT=.venv-source uv sync --locked --no-build --no-install-project

# Prepares the existing application and disposable database on execution hosts.
setup:
    bun run setup
    just setup-source

# Runs every independent source check without generation, compilation or tests.
check:
    just --fmt --check
    cmp --silent .bun-version <(bun --version)
    actionlint
    zizmor --offline --no-progress .github
    cd frontend && bun x --no-install oxfmt --check
    backend/.venv-source/bin/ruff format --check backend tools/ci.py tools/check-generated.py tools/test_secret_ignore.py
    backend/.venv-source/bin/ruff check backend tools/ci.py tools/check-generated.py tools/test_secret_ignore.py
    cd backend && .venv-source/bin/mypy
    betterleaks git --no-banner --redact .

# Applies source formatting and automatic lint fixes.
fix:
    just --fmt
    cd frontend && bun x --no-install oxfmt
    backend/.venv-source/bin/ruff format backend tools/ci.py tools/check-generated.py tools/test_secret_ignore.py
    backend/.venv-source/bin/ruff check --fix backend tools/ci.py tools/check-generated.py tools/test_secret_ignore.py

# Runs generated prerequisites, type/contract checks and the existing test suites.
test:
    python3 -B -m unittest discover -s tools -p test_secret_ignore.py
    bun run check
    bun run test

# Builds both existing application artifacts.
build:
    bun run build

# Exercises real auth/RBAC and backend tests in the existing disposable database.
integration:
    bun run test:integration

# Regenerates the existing contract/client and refuses any tracked or new drift.
generated:
    bun run api:generate
    python3 tools/check-generated.py

# Builds the existing backend container on execution hosts.
container:
    docker build -t vibestrap-backend:ci backend

# Scans the frozen dependency graph without installing or changing packages.
security:
    osv-scanner scan source --recursive .

# Runs the complete application verification used by CI.
[private]
verify-application: check test build integration generated container

# Runs every source, native, generated, integration, image and vulnerability gate.
verify: verify-application security

# Runs the complete existing job lifecycle with resource cleanup on every ordinary outcome.
ci:
    python3 tools/ci.py
