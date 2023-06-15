import asyncio
import shutil
from pathlib import Path
from typing import List

from utils import (
    run_subprocess,
    upload_sources,
    make_requirements_hash,
    CID,
)


async def build_and_upload_requirements_python(
    requirements: List[str],
) -> CID:
    opt_packages = Path(
        "/opt/packages"
    )  # /opt/packages is by default imported into Aleph VMs
    # check if directory exists, clean if necessary
    if not opt_packages.exists():
        opt_packages.mkdir(parents=True, exist_ok=True)
    else:
        shutil.rmtree(opt_packages)
        opt_packages.mkdir(parents=True, exist_ok=True)

    requirements_hash = make_requirements_hash(requirements)

    mksquashfs_dir = Path(f"/opt/sqashfs/")
    mksquashfs_dir.mkdir(parents=True, exist_ok=True)
    squashfs_path = mksquashfs_dir / Path(f"{requirements_hash}.squashfs")
    await run_subprocess(f"pip install -t {str(opt_packages)} {' '.join(requirements)}")
    await run_subprocess(f"mksquashfs {str(opt_packages)} {squashfs_path}")
    (_, cid) = await asyncio.gather(
        run_subprocess(f"rm -rf {str(opt_packages)}"),
        upload_sources(Path(squashfs_path)),
    )
    await run_subprocess(f"rm -rf {squashfs_path}")
    return cid


async def build_and_upload_node_modules(
    modules: List[str],
) -> CID:
    root_modules = Path(
        "/root/.node_modules"
    )  # /root/.node_modules is by default searched by NodeJS for modules running as root
    # check if directory exists, clean if necessary
    if not root_modules.exists():
        root_modules.mkdir(parents=True, exist_ok=True)
    else:
        shutil.rmtree(root_modules)
        root_modules.mkdir(parents=True, exist_ok=True)

    modules_hash = make_requirements_hash(modules)

    mksquashfs_dir = Path("/opt/sqashfs/")
    mksquashfs_dir.mkdir(parents=True, exist_ok=True)
    squashfs_path = mksquashfs_dir / Path(f"{modules_hash}.squashfs")
    await run_subprocess(f"npm install --prefix {str(root_modules)} {' '.join(modules)}")
    await run_subprocess(f"mv {str(root_modules)}/node_modules/* {str(root_modules)}")
    await run_subprocess(f"rm -rf {str(root_modules)}/node_modules")
    await run_subprocess(f"mksquashfs {str(root_modules)} {squashfs_path}")
    (_, cid) = await asyncio.gather(
        run_subprocess(f"rm -rf {str(root_modules)}"),
        upload_sources(Path(squashfs_path)),
    )
    await run_subprocess(f"rm -rf {squashfs_path}")
    return cid
