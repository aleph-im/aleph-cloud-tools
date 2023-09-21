"""
This is the Aleph Console Backend VM. Its current primary purpose is to accept a list of python or node.js dependencies
and to dependency_builder the according immutable IPFS volume.
"""
import logging
import time
from pathlib import Path
from typing import List

from aleph.sdk.vm.app import AlephApp
from build import (build_and_upload_cid, build_and_upload_node_modules,
                   build_and_upload_node_package,
                   build_and_upload_python_pipfile,
                   build_and_upload_python_pyproject,
                   build_and_upload_python_requirements)
from fastapi import FastAPI, File, UploadFile
from starlette.middleware.cors import CORSMiddleware
from utils import CID, save_file

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
async def build_python3_9(requirements: List[str]) -> CID:
    """Build a python 3.9 environment."""
    return await build_and_upload_python_requirements(requirements)


@app.post("/build/python3.9/requirements")
async def build_python3_9_requirements(
    data_file: UploadFile = File(...),
) -> CID:
    """Build a python 3.9 environment from a requirements.txt file."""
    requirements = data_file.file.read().decode("utf-8").split("\n")
    requirements = [r.strip() for r in requirements if r]
    return await build_and_upload_python_requirements(requirements)


@app.post("/build/python3.9/pipfile")
async def build_python3_9_pipfile(
    data_file: UploadFile = File(...),
) -> CID:
    """Build a python 3.9 environment from a Pipfile file."""
    path = Path(f"/opt/{str(time.time())}/Pipfile")
    await save_file(data_file, path)
    return await build_and_upload_python_pipfile(path)


@app.post("/build/python3.9/pyproject")
async def build_python3_9_pyproject(
    data_file: UploadFile = File(...),
) -> CID:
    """Build a python 3.9 environment from a pyproject.toml file."""
    path = Path(f"/opt/{str(time.time())}/pyproject.toml")
    await save_file(data_file, path)
    return await build_and_upload_python_pyproject(path)


@app.post("/build/nodejs")
async def build_nodejs(modules: List[str]) -> CID:
    """Build a node.js environment."""
    return await build_and_upload_node_modules(modules)


@app.post("/build/nodejs/package")
async def build_nodejs_package(
    data_file: UploadFile = File(...),
) -> CID:
    """Build a node.js environment from a package.json file."""
    path = Path(f"/opt/{str(time.time())}/package.json")
    await save_file(data_file, path)
    return await build_and_upload_node_package(path)


@app.post("/build/cid")
async def build_squashfs_from_cid(cid: str) -> CID:
    """Build a squashfs from a CID pointing to a directory on IPFS."""
    return await build_and_upload_cid(cid=cid)
