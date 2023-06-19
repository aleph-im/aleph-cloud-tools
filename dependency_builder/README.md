# Dependency Volume Builder
This service exposes an API to build a volume with all the dependencies needed to run a program on an Aleph VM. The volume is subsequently deployed to IPFS and its CID returned.

## Supported languages
The API currently supports the following inputs:
- Python
  - List of dependencies (pip install)
  - requirements.txt
  - Pipfile
  - pyproject.toml
- Node.js
  - List of dependencies (npm install)
  - package.json

## Usage
Simply upload your file to the appropriate endpoint and the service will return the CID of the volume containing the dependencies.
If you choose to upload a list of dependencies, the service will use that as an argument to the package manager and build the volume as if you had run the command locally.

## Run locally
To run the service locally, you need to have `docker` and `docker-compose` installed, then simply run:
```shell
docker-compose up --build
```
The API will be available on `http://localhost:8000`.

## Troubleshooting
Common errors that can arise when building the volume:
1. The passed dependencies are not valid. Make sure that the list of dependencies or file you are passing can be installed locally with either **python3.9** or **node v16**.
2. The service is not able to connect to IPFS. In that case, retry after a few minutes.
3. The request takes unusually long to complete (2-5 minutes). This can happen with very large dependencies. Just be patient and wait for the request to complete.