from aexpy.services.workers import DockerWorkerServiceProvider


def getService():
    return DockerWorkerServiceProvider(tag="latest")
