import os

from hoover.search.tracing import init_tracing


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "liquidcore.site.settings")

    init_tracing('gunicorn')
