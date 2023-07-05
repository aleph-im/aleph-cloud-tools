FROM python:3.9-slim-bullseye as python-base

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3-pip squashfs-tools debootstrap

COPY . .

RUN ./create_disk_image.sh

CMD ["/bin/bash"]
