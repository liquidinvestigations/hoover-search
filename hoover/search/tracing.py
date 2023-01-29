"""Tracing integration library.

Provides init functions for hooking into different entry points, as well the ability to
wrap functions and create custom spans.
"""
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
# disabled because of error "TypeError: 'HttpHeaders' object does not support item assignment"
# from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.elasticsearch import ElasticsearchInstrumentor
# commented out because of leaked socket warning, but it seems to be harmless as it uses same fd
# from opentelemetry.instrumentation.celery import CeleryInstrumentor

SERVICE_NAME = "hoover-search"
SERVICE_VERSION = subprocess.check_output("git describe --tags --always", shell=True).decode().strip()

log = logging.getLogger(__name__)

local = threading.local()


def init_tracing(_from):
    """Initialize tracing at the beginning of an entry point, like manage.py, celery or gunicorn.

    The _from argument is logged at the command line.
    """
    log.info('FROM %s: initializing trace engine for %s %s...', _from, SERVICE_NAME, SERVICE_VERSION)
    if os.getenv('UPTRACE_DSN'):
        uptrace.configure_opentelemetry(
            service_name=SERVICE_NAME,
            service_version=SERVICE_VERSION,
        )
        LoggingInstrumentor().instrument(set_logging_format=True)
        Psycopg2Instrumentor().instrument(skip_dep_check=True)
        DjangoInstrumentor().instrument()
        # RequestsInstrumentor().instrument()
        ElasticsearchInstrumentor().instrument()
        # CeleryInstrumentor().instrument()


class Tracer:
    """Tracing handler with simplified interface.

    Manages shutdown of opentelemetry tracing objects after use, by using thread-local storage
    to keep track of when we created the object.
    """
    def __init__(self, name, version=None):
        """Construct tracer with name and version."""
        self.name = name
        self.version = version or SERVICE_VERSION

    @contextmanager
    def span(self, *args, **kwds):
        """Call the opentelemetry start_as_current_span() context manager and manage shutdowns.
        """
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
                try:
                    trace.get_tracer_provider().force_flush()
                    trace.get_tracer_provider().shutdown()
                # the ProxyTracerProvider we get when no tracing is configured
                # doesn't have these methods.
                except AttributeError:
                    pass
                except Exception as e:
                    log.warning('tracer shutdown exception: ' + str(e))
                finally:
                    local.tracer = None

    def wrap_function(self):
        """Returns a function wrapper that has a telemetry span around the function.
        """
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
