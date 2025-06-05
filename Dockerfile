FROM python:3.11-alpine

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml poetry.lock* requirements.txt ./

# Install Poetry and dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-root || pip install -r requirements.txt

# Copy all Python source files
COPY *.py ./

ENTRYPOINT ["python", "bot.py"]

