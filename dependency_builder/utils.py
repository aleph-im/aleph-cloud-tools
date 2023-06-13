import asyncio
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Optional, List

from aleph.sdk import AuthenticatedAlephClient
from aleph.sdk.types import StorageEnum
from aleph_message.models import StoreMessage
from aleph_message.status import MessageStatus


SOURCES_CHANNEL = "sources"


async def run_subprocess(
    cmd: str,
    logger: logging.Logger = logging.getLogger(__name__)
) -> (bytes, bytes, int):
    """Runs a subprocess and awaits its result."""
    proc = await asyncio.create_subprocess_exec(
        *cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return_code = proc.returncode
    if return_code != 0:
        logger.error(
            f"Command {cmd} failed with return code {return_code}"
            f"stdout: {stdout.decode('utf-8')}"
            f"stderr: {stderr.decode('utf-8')}"
        )
    return stdout, stderr, return_code


def make_requirements_hash(requirements: List[str]) -> str:
    """Makes a hash from a list of requirements."""
    return hashlib.sha256("\n".join(requirements).encode("utf-8")).hexdigest()


async def upload_sources(
    session: AuthenticatedAlephClient,
    path: Path,
    tags: Optional[List[str]] = None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> StoreMessage:
    """Uploads a file to IPFS and returns the StoreMessage."""
    logger.debug(f"Reading {path}...")
    with open(path, "rb") as fd:
        file_content = fd.read()
    logger.debug(f"Uploading {path} to IPFS...")
    store_message, status = await session.create_store(
        file_content=file_content,
        storage_engine=StorageEnum.ipfs,
        channel=SOURCES_CHANNEL,
        guess_mime_type=True,
        extra_fields={
            "tags": tags,
        } if tags else None,
    )
    if status in [MessageStatus.PENDING, MessageStatus.PROCESSED]:
        logger.debug(f"{path} upload finished")
        return store_message

    logger.error(f"{path} upload failed")
