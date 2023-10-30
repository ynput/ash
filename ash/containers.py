import os

from nxtools import logging

PODMAN = os.getenv("AYON_USE_PODMAN", False)

DOCKER_HOST = os.getenv("DOCKER_HOST", None)

if not DOCKER_HOST:
    DOCKER_HOST = os.getenv("CONTAINER_HOST", None)

if not DOCKER_HOST:
    if PODMAN:
        DOCKER_HOST = "unix:///run/user/1000/podman/podman.sock"
    else:
        DOCKER_HOST = "unix://var/run/docker.sock"


def get_container_client():
    """Creates a Client connection to the Socket 

    Depending on teh container runtime we use, it will import and
    create the class acordingly.

    Note that podman does not require the "APIClient" to inspect `Containers.`

    Returns:
        tuple(client, api): The Client object, and in case of Docker the APIClient.
    """
    client = None
    api = None

    if PODMAN:
        from podman import PodmanClient
        client = PodmanClient(base_url=DOCKER_HOST)
        logging.info("Using container client: Podman")
    else:
        from docker import APIClient, DockerClient
        client = DockerClient(base_url=DOCKER_HOST)
        api = APIClient(base_url=DOCKER_HOST)
        logging.info("Using container client: Docker")

    return client, api
