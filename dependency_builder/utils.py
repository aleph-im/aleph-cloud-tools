import asyncio
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, NewType

import aioipfs
from aleph.sdk import AuthenticatedAlephClient
from aleph_message.models import StoreMessage
from aleph_message.status import MessageStatus

Multiaddr = NewType("Multiaddr", str)
CID = NewType("CID", str)


async def run_subprocess(
    cmd: str, logger: logging.Logger = logging.getLogger(__name__)
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
    path: Path,
    logger: logging.Logger = logging.getLogger(__name__),
) -> CID:
    """Uploads a file to IPFS and returns the StoreMessage."""
    logger.debug(f"Reading {path}...")
    with open(path, "rb") as fd:
        file_content = fd.read()
    logger.debug(f"Uploading {path} to IPFS...")
    cid = await upload_files_to_ipfs([path], logger=logger)
    return cid


def raise_no_cid():
    raise ValueError("Could not obtain a CID")


async def upload_files_to_ipfs(
    files: list[Path],
    multiaddr: Multiaddr = Multiaddr("/dns6/ipfs-2.aleph.im/tcp/443/https"),
    logger: logging.Logger = logging.getLogger(__name__),
) -> CID:
    client = aioipfs.AsyncIPFS(maddr=multiaddr)

    try:
        cid = None
        async for added_file in client.add(*files, recursive=True):
            logger.debug(
                f"Uploaded file {added_file['Name']} with CID: {added_file['Hash']}"
            )
            cid = added_file["Hash"]
        # The last CID is the CID of the directory uploaded
        return cid or raise_no_cid()
    finally:
        await client.close()
