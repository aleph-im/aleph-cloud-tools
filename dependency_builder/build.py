import asyncio
import shutil
from pathlib import Path
from typing import List

from aleph.sdk import AuthenticatedAlephClient
from aleph_message.models import StoreMessage, MessageType

from utils import run_subprocess, upload_sources, make_requirements_hash, SOURCES_CHANNEL


async def build_and_upload_requirements_python(
    session: AuthenticatedAlephClient,
    requirements: List[str],
) -> StoreMessage:
    opt_packages = Path(
        "/opt/packages"
    )  # /opt/packages is by default imported into Python
    # check if directory exists, clean if necessary
    if not opt_packages.exists():
        opt_packages.mkdir(parents=True, exist_ok=True)
    else:
        shutil.rmtree(opt_packages)
        opt_packages.mkdir(parents=True, exist_ok=True)

    requirements_hash = make_requirements_hash(requirements)

    # check if requirements are already uploaded
    resp = await session.get_messages(
        message_type=MessageType.store, tags=[requirements_hash], channels=[SOURCES_CHANNEL]
    )
    if resp.messages:
        return resp.messages[0]

    # install requirements, dependency_builder & upload squashfs, clean up
    mksquashfs_dir = Path("/opt/mysqashfs/")
    mksquashfs_dir.mkdir(parents=True, exist_ok=True)
    squashfs_path = mksquashfs_dir / Path(f"{requirements_hash}.squashfs")
    await run_subprocess(f"pip install -t {str(opt_packages)} {' '.join(requirements)}")
    await run_subprocess(f"mksquashfs {str(opt_packages)} {squashfs_path}")
    (_, store_message) = await asyncio.gather(
        run_subprocess(f"rm -rf {str(opt_packages)}"),
        upload_sources(session, Path(squashfs_path), tags=[requirements_hash]),
    )
    await run_subprocess(f"rm -rf {squashfs_path}")
    return store_message


async def build_and_upload_node_dependencies(
    session: AuthenticatedAlephClient,
    package_json: str,
) -> StoreMessage:
    # TODO: implement
    raise NotImplementedError
