import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import List

from fastapi import HTTPException
from utils import (CID, download_from_ipfs, make_dependencies_hash,
                   run_subprocess, upload_sources)

# /opt/packages is by default imported into Python Aleph VMs
PACKAGES_PATH = Path("/opt/packages")

# /opt/node_modules is by default imported into Node.js Aleph VMs
MODULES_PATH = Path("/opt/node_modules")

# /opt/root is just a placeholder here, the resulting squashfs can be mounted on any path
ROOT_PATH = Path("/opt/root")


async def mksquashfs(source, destination):
    await run_subprocess(f"mksquashfs {str(source)} {str(destination)} -noappend")


async def prepare_paths(dependencies_path: Path, dependencies_hash: str):
    """Prepares the paths for the dependencies and returns the path to the squashfs file."""
    # check if directory exists, clean if necessary
    if not dependencies_path.exists():
        dependencies_path.mkdir(parents=True, exist_ok=True)
    else:
        shutil.rmtree(dependencies_path)
        dependencies_path.mkdir(parents=True, exist_ok=True)
    mksquashfs_dir = Path("/opt/sqashfs/")
    mksquashfs_dir.mkdir(parents=True, exist_ok=True)
    squashfs_path = mksquashfs_dir / Path(f"{dependencies_hash}.squashfs")
    return squashfs_path


async def build_and_upload_python_requirements(
    requirements: List[str],
) -> CID:
    dependencies_hash = make_dependencies_hash(requirements)
    squashfs_path = await prepare_paths(PACKAGES_PATH, dependencies_hash)
    try:
        await run_subprocess(
            f"pip install -t {str(PACKAGES_PATH)} {' '.join(requirements)}"
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Unprocessable requirements: {e.stderr}",
        )
    await mksquashfs(PACKAGES_PATH, squashfs_path)
    (_, cid) = await asyncio.gather(
        run_subprocess(f"rm -rf {str(PACKAGES_PATH)}"),
        upload_sources(Path(squashfs_path)),
    )
    await run_subprocess(f"rm -rf {squashfs_path}")
    return cid


async def build_and_upload_python_pipfile(
    pipfile_path: Path,
) -> CID:
    with open(pipfile_path, "r") as fd:
        pipfile = fd.read()
    dependencies_hash = make_dependencies_hash(pipfile.split("\n"))
    squashfs_path = await prepare_paths(PACKAGES_PATH, dependencies_hash)
    try:
        await run_subprocess(
            f"cd {pipfile_path.parent} && pipenv lock && pipenv requirements > requirements.txt"
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Unprocessable pipfile: {e.stderr}",
        )
    await run_subprocess(
        f"pip install -t {str(PACKAGES_PATH)} -r {str(pipfile_path.parent / Path('requirements.txt'))}"
    )
    await mksquashfs(PACKAGES_PATH, squashfs_path)
    (_, _, cid) = await asyncio.gather(
        run_subprocess(f"rm -rf {str(pipfile_path.parent)}"),
        run_subprocess(f"rm -rf {str(PACKAGES_PATH)}"),
        upload_sources(Path(squashfs_path)),
    )
    await run_subprocess(f"rm -rf {squashfs_path}")
    return cid


async def build_and_upload_python_pyproject(
    pyproject_path: Path,
) -> CID:
    with open(pyproject_path, "r") as fd:
        pyproject = fd.read()
    dependencies_hash = make_dependencies_hash(pyproject.split("\n"))
    squashfs_path = await prepare_paths(PACKAGES_PATH, dependencies_hash)
    try:
        await run_subprocess(
            f"cd {pyproject_path.parent} && poetry export -f requirements.txt -o requirements.txt --without-hashes"
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Unprocessable pyproject.toml: {e.output}",
        )
    await run_subprocess(
        f"pip install -t {str(PACKAGES_PATH)} -r {str(pyproject_path.parent / Path('requirements.txt'))}"
    )
    await mksquashfs(PACKAGES_PATH, squashfs_path)
    (_, _, cid) = await asyncio.gather(
        run_subprocess(f"rm -rf {str(pyproject_path.parent)}"),
        run_subprocess(f"rm -rf {str(PACKAGES_PATH)}"),
        upload_sources(Path(squashfs_path)),
    )

    await run_subprocess(f"rm -rf {squashfs_path}")
    return cid


async def build_and_upload_node_modules(
    modules: List[str],
) -> CID:
    dependencies_hash = make_dependencies_hash(modules)
    squashfs_path = await prepare_paths(MODULES_PATH, dependencies_hash)
    try:
        await run_subprocess(f"npm install -g {' '.join(modules)}")
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid packages: {e.output}",
        )
    await run_subprocess(f"mv /usr/local/lib/node_modules {str(MODULES_PATH)}")
    await mksquashfs(MODULES_PATH, squashfs_path)
    (_, _, cid) = await asyncio.gather(
        run_subprocess("rm -rf /usr/local/lib/node_modules"),
        run_subprocess(f"rm -rf {str(MODULES_PATH)}"),
        upload_sources(Path(squashfs_path)),
    )
    await run_subprocess(f"rm -rf {squashfs_path}")
    return cid


async def build_and_upload_node_package(
    packages_path: Path,
) -> CID:
    with open(packages_path, "r") as fd:
        packages = fd.read()
    dependencies_hash = make_dependencies_hash(packages.split("\n"))
    squashfs_path = await prepare_paths(MODULES_PATH, dependencies_hash)
    await run_subprocess(f"mv {str(packages_path)} {str(MODULES_PATH)}")
    try:
        await run_subprocess(f"cd {str(MODULES_PATH)} && npm install")
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid package.json: {e.output}",
        )
    await mksquashfs(MODULES_PATH, squashfs_path)
    (_, _, cid) = await asyncio.gather(
        run_subprocess(f"rm -rf {str(MODULES_PATH)}"),
        run_subprocess(f"rm -rf {str(packages_path.parent)}"),
        upload_sources(Path(squashfs_path)),
    )
    await run_subprocess(f"rm -rf {squashfs_path}")
    return cid


async def build_and_upload_cid(
    cid: str,
) -> CID:
    """Builds a squashfs from an IPFS CID referencing a directory."""

    squashfs_path = await prepare_paths(ROOT_PATH, cid)
    await download_from_ipfs(CID(cid), ROOT_PATH)
    await mksquashfs(ROOT_PATH, squashfs_path)
    (_, squashfs_cid) = await asyncio.gather(
        run_subprocess(f"rm -rf {str(ROOT_PATH)}"),
        upload_sources(Path(squashfs_path)),
    )
    await run_subprocess(f"rm -rf {squashfs_path}")
    return squashfs_cid
