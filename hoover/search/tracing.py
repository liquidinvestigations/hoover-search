import functools
import threading
import os
import subprocess
import logging
from contextlib import contextmanager

import uptrace
from opentelemetry import trace
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.elasticsearch import ElasticsearchInstrumentor

SERVICE_NAME = "hoover-search"
SERVICE_VERSION = subprocess.check_output("git describe --tags", shell=True).decode().strip()

log = logging.getLogger(__name__)

local = threading.local()


def init_tracing(_from):
    log.info('FROM %s: initializing trace engine for %s %s...', _from, SERVICE_NAME, SERVICE_VERSION)
    if os.getenv('UPTRACE_DSN'):
        uptrace.configure_opentelemetry(
            service_name=SERVICE_NAME,
            service_version=SERVICE_VERSION,
        )
        LoggingInstrumentor().instrument(set_logging_format=True)
        Psycopg2Instrumentor().instrument(skip_dep_check=True)
        DjangoInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        ElasticsearchInstrumentor().instrument()


class Tracer:
    def __init__(self, name, version=None):
        self.name = name
        self.version = version or SERVICE_VERSION
        # the module level assignment only works for the main thread, others need to be updated on the fly here
        global local
        local.tracer = None

    @contextmanager
    def span(self, *args, **kwds):
        global local
        we_are_first = getattr(local, 'tracer', None) is None
        if we_are_first:
            local.tracer = trace.get_tracer(self.name, self.version)
            log.debug('creating tracer for module %s...', self.name)
        try:
            with local.tracer.start_as_current_span(*args, **kwds) as span:
                yield span
        finally:
            if we_are_first:
                log.debug('destroying tracer for module %s...', self.name)
                trace.get_tracer_provider().force_flush()
                trace.get_tracer_provider().shutdown()
                local.tracer = None

    def wrap_function(self):
        def decorator(function):
            fname = self.name + '.' + function.__qualname__
            log.debug('initializing trace for function %s...', fname)

            @functools.wraps(function)
            def wrapper(*k, **v):
                with self.span(fname) as _:
                    log.debug('executing traced function %s...', fname)
                    return function(*k, **v)
            return wrapper
        return decorator
