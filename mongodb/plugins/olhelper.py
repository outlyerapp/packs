def exec_run(id=None, command=None):
    """Some docs"""
    import docker
    client = docker.from_env()
    target = client.containers.get(id)
    return target.exec_run(command)


