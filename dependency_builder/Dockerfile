FROM python:3.9-slim-buster as python-base

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs

# Verify Node.js and npm installation
RUN node --version
RUN npm --version

WORKDIR /app

COPY poetry.lock .
COPY pyproject.toml .
RUN pip install poetry pipenv
RUN poetry install
RUN apt-get update && \
    apt-get install -y python3-pip squashfs-tools

COPY . .
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
