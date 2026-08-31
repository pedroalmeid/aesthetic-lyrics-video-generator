FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends ffmpeg fonts-dejavu-core \
    && apt-get clean && rm -rf /var/lib/apt/lists/*