"""
This is the Aleph Console Backend VM. Its current primary purpose is to accept a list of python or node.js dependencies
and to dependency_builder the according immutable IPFS volume.
"""
import logging
from typing import List

from aleph.sdk.client import AuthenticatedAlephClient
from aleph.sdk.chains.ethereum import get_fallback_account
from aleph.sdk.conf import settings
from aleph.sdk.vm.app import AlephApp
from aleph_message.models import StoreMessage
from fastapi import FastAPI, UploadFile, File
from starlette.middleware.cors import CORSMiddleware

from build import build_and_upload_requirements_python

logger = (
    logging.getLogger(__name__)
    if __name__ != "__main__"
    else logging.getLogger("uvicorn")
)
http_app = FastAPI()
http_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = AlephApp(http_app)


@app.get("/")
async def index():
    return "Call /docs for the API documentation."


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/build/python3.9")
async def build_python3_9(requirements: List[str]) -> StoreMessage:
    """Build a python 3.9 environment."""
    aleph_client = AuthenticatedAlephClient(get_fallback_account(), settings.API_HOST)
    return await build_and_upload_requirements_python(aleph_client, requirements)


@app.post("/build/python3.9/requirements")
async def build_python3_9_requirements(data_file: UploadFile = File(...)) -> StoreMessage:
    """Build a python 3.9 environment from a requirements.txt file."""
    aleph_client = AuthenticatedAlephClient(get_fallback_account(), settings.API_HOST)
    requirements = data_file.file.read().decode("utf-8").split("\n")
    requirements = [r.strip() for r in requirements if r]
    return await build_and_upload_requirements_python(aleph_client, requirements)
