import asyncio
import hashlib
import logging
import shutil
import subprocess
from pathlib import Path
from typing import List, NewType

import aioipfs
from fastapi import HTTPException

Multiaddr = NewType("Multiaddr", str)
CID = NewType("CID", str)


async def run_subprocess(
    cmd: str, logger: logging.Logger = logging.getLogger(__name__)
) -> (str, str, int):
    """Runs a subprocess and awaits its result."""
    logger.debug("[COMMAND]", cmd)
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return_code = proc.returncode
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    if return_code != 0:
        logger.error(
            f"Command {cmd} failed with return code {return_code}"
            f"stdout: {stdout}"
            f"stderr: {stderr}"
        )
        raise subprocess.CalledProcessError(return_code, cmd, stderr)
    logger.debug(
        "\n[RETURN CODE]",
        return_code,
        "\n[STDOUT]",
        stdout,
        "\n[STDERR]",
        stderr,
    )
    return stdout, stderr, return_code


def make_dependencies_hash(dependencies: List[str]) -> str:
    """Makes a hash from a list of requirements."""
    return hashlib.sha256(
        "\n".join(sorted(set(dependencies))).encode("utf-8")
    ).hexdigest()


async def upload_sources(
    path: Path,
    logger: logging.Logger = logging.getLogger(__name__),
) -> CID:
    """Uploads a file to IPFS and returns the StoreMessage."""
    logger.debug(f"Uploading {path} to IPFS...")
    try:
        cid = await upload_files_to_ipfs([path], logger=logger)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not upload {path} to IPFS: {e}",
        )
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


async def save_file(data_file, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(data_file.file, buffer)
