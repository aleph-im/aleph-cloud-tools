FROM python:3.9

WORKDIR /app

COPY poetry.lock .
COPY pyproject.toml .
RUN pip install poetry
RUN poetry install
RUN apt-get update && \
    apt-get install -y python3-pip squashfs-tools npm

COPY . .
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
