FROM python:3.9-slim-buster as python-base

WORKDIR /app

COPY poetry.lock .
COPY pyproject.toml .

RUN apt-get update && \
    apt-get install -y python3-pip squashfs-tools

RUN pip install poetry

RUN poetry install

COPY . .
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
