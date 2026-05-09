# Setup script for the project, to make it easy to work on a git worktree for instance.

# Exit immediately if a command exits with a non-zero status,
# or if a variable is used but not set
set -eu

# 0. Setup virtual environment
if [ ! -d "venv" ]; then
    uv venv venv --python 3.12
fi
source ./venv/bin/activate
uv pip install -r ./requirements/prod.txt
echo "✅ Virtualenv created and dependencies installed."

################################################
# 1. Clean up docker
docker system prune -f

################################################
# 2. Create an .env file with SECRET_KEY and ADMIN_SITE_URL variables

# ./setup_env_file.sh

echo "✅ settings/env created."

################################################
# 3. Create Postgres (with pgvector) container, stopping it if it is already running

if docker ps --format '{{.Names}}' | grep -qw "postgres"; then
    echo "💡 Postgres container is already running. Stopping it."
    docker rm -f postgres
fi

docker run --rm --name postgres \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=postgres \
    -p 5434:5432 \
    -d ankane/pgvector

echo "✅ Postgres (pgvector) container created and running."

# Wait for Postgres to be ready
until docker exec postgres pg_isready -U postgres; do
    echo "⏳ Waiting for Postgres to be ready..."
    sleep 1
done

# Enable pgvector extension
echo "🔧 Creating pgvector extension..."
docker exec postgres \
    psql -U postgres -d postgres \
    -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "✅ pgvector extension is enabled."

################################################
# 4. Create Redis container, stopping it if it is already running

if docker ps -a --format '{{.Names}}' | grep -wq redis; then
    echo "💡 Redis container is already running. Stopping it."
    docker rm -f redis
fi

docker run -d --rm --name redis -p 6379:6379 redis
echo "✅ Redis container created and running."

################################################
# 5. Perform Django migrations

if ! uv run --active python manage.py makemigrations --dry-run --check; then
	echo "❌ Couldn't run makemigrations!"
	exit 1
fi

uv run --active python manage.py migrate
echo "✅ Django migrations performed."

################################################
# 6. Collect static files

uv run --active python manage.py collectstatic --noinput

echo "✅ Static files collected."

################################################
# 7. Compile messages

# uv run python manage.py compilemessages --ignore=.venv

# echo "✅ Messages compiled."

################################################
# 8. Create test data for all apps

# uv run python manage.py refresh_synthetic_data
# echo "✅ Synthetic data refreshed on configured database."

################################################
# 9. Setup periodic tasks
# uv run python manage.py setup_periodic_tasks
# echo "✅ Periodic tasks setup finished."

################################################
# 10. Create superuser
export DJANGO_SUPERUSER_EMAIL='...'
export DJANGO_SUPERUSER_PASSWORD='...'
uv run --active python manage.py setup_local_synthetic_data

################################################
# 11. Install pre-commit hooks for the project and check them

pre-commit install
pre-commit run --all-files
echo "✅ Pre-commit hooks installed and checked."

################################################
# 12. Done
echo "✅ Setup is complete."
