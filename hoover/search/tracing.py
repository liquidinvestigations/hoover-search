# flake8: noqa
"""Tracing integration library.
Provides init functions for hooking into different entry points, as well the ability to
wrap functions and create custom spans.
"""

import logging
import functools
import subprocess
from contextlib import contextmanager
from time import time
import threading
import queue
import sys
import os


# fix PYTHONPATH env for the auto-instrumentation
os.environ['PYTHONPATH'] = (
    (os.environ.get('PYTHONPATH', '') + ':') if os.environ.get('PYTHONPATH') else ''
) + ':'.join(sys.path)
log = logging.getLogger(__name__)


try:
    assert os.environ.get('TRACING_ENABLED'), 'tracing not enabled'
    from opentelemetry.instrumentation.auto_instrumentation.sitecustomize import initialize
    initialize()
    from opentelemetry import metrics, trace  # noqa: E402 -- needs to happen after initialize
    ENABLED = True
except Exception as e:
    log.debug(e)
    log.debug('could not init tracing; moving on.')
    trace = None
    metrics = None
    ENABLED = False


SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", '')
SERVICE_VERSION = os.environ.get('OTEL_SERVICE_VERSION', '')

MAX_KEY_LEN = 63
"""Max key length for open telemetry counters, span names and other identifiers."""

MAX_COUNTER_KEY_LEN = 14
"""Max key reserved for counter suffixes."""

UPLOAD_DELAY_SECONDS = 15
"""Flush the spans storage once every this amount of seconds."""

COUNTER_QUEUE_SIZE = 5000
"""Max size of queue where count events are stored."""


def shorten_name(string, length):
    """Shortens a string to fit under some length.
    This is needed because opentelemetry key length limit are 64,
    and will fail in various ways if they're not.
    """
    if len(string) <= length:
        return string
    half_len = int((length - 5) / 2)
    string = string[:half_len] + '...' + string[-half_len + 1:]
    assert len(string) <= length
    return string


class FakeSpan:
    def __getattr__(self, *a, **kw):
        return self

    def __call__(self, *a, **kw):
        return 'fakeSpan'

    def __bool__(self):
        return True


class Tracer:
    """Tracing handler with simplified interface.
    Manages flush of opentelemetry tracing objects after use.
    """
    def __init__(self, name, version=None):
        """Construct tracer with name and version.
        """
        name = name.replace(' ', '_')
        self.name = name
        self.version = version or SERVICE_VERSION
        self.last_upload_time = time()
        if ENABLED:
            self.tracer = trace.get_tracer(self.name, self.version)
            self.counter_queue = queue.Queue(COUNTER_QUEUE_SIZE)
            self.counter_thread = threading.Thread(target=self.counter_worker, daemon=True)
            self.counter_thread.start()
        else:
            self.tracer = None
            self.counter_queue = None
            self.counter_thread = None

    @contextmanager
    def span(self, name, *args, attributes={}, extra_counters={}, **kwds):
        """Call the opentelemetry start_as_current_span() context manager and manage shutdowns.
        """
        if not ENABLED:
            yield FakeSpan()
            return

        name = name.replace(' ', '_')
        if not name.startswith(self.name):
            name = self.name + '.' + name
        name = shorten_name(name, MAX_KEY_LEN - MAX_COUNTER_KEY_LEN - 4)  # -2 for the __
        log.debug('creating tracer for module=%s with name=%s...', self.name, name)

        attributes = self._populate_attributes(attributes)
        self.count(name + '__hits', attributes=attributes)
        for key, value in extra_counters.items():
            assert len(key) <= MAX_COUNTER_KEY_LEN, 'counter key too long!'
            self.count(name + '__' + key, value=value['value'], attributes=attributes, unit=value['unit'])
        try:
            with self.tracer.start_as_current_span(name, *args, **kwds) as span:
                t0 = time()
                yield span
        except Exception as e:
            log.error('span filed: %s', name)
            log.exception(e)
            raise e
        finally:
            self.count(name + '__duration', value=time() - t0, attributes=attributes, unit='s')
            log.debug('destroying tracer for module %s...', self.name)
            try:
                # flush data with timeout of 30s
                if self.last_upload_time + UPLOAD_DELAY_SECONDS < time():
                    t0 = time()
                    trace.get_tracer_provider().force_flush(500)
                    log.debug(self.name + ': uploading stats took ' + str(round(time() - t0, 3)) + 's')
                    self.last_upload_time = time()
            # the ProxyTracerProvider we get when no tracing is configured
            # doesn't have these methods.
            except AttributeError:
                pass
            except Exception as e:
                log.warning('tracer flush exception: ' + str(e))

    def wrap_function(self):
        """Returns a function wrapper that has a telemetry span around the function.
        """
        def decorator(function):
            if not ENABLED:
                return function

            fname = self.name + '.' + function.__qualname__
            log.debug('initializing trace for function %s...', fname)

            @functools.wraps(function)
            def wrapper(*k, **v):
                with self.span(fname) as _:
                    log.debug('executing traced function %s...', fname)
                    return function(*k, **v)
            return wrapper
        return decorator

    def _count(self, meter, counters, key, value=1, attributes={}, description='', unit="1", **kwds):
        """Helper for the opentelemetry "_metrics" counter.
        """
        key = key.replace(' ', '_')
        # log.debug('count: ' + key)
        assert len(key) <= MAX_KEY_LEN, 'counter name too long!'

        try:
            if key not in counters:
                counters[key] = meter.create_counter(
                    name=key, description=description, unit=unit)
            attributes = self._populate_attributes(attributes)
            counters[key].add(value, attributes=attributes)
        except Exception as e:
            log.error('failed to increment count for counter %s: %s', key, str(e))

    def count(self, key, value=1, attributes={}, description='', unit="1", **kwds):
        if not ENABLED:
            return

        args = (key, value, attributes, description, unit, kwds)
        try:
            self.counter_queue.put(args, block=False)
        except Exception as e:
            log.error(e)
            log.warning('counter queue full: ' + self.name)

    def counter_worker(self):
        if not ENABLED:
            return
        counters = {}
        meter = metrics.get_meter(self.name)
        while True:
            (key, value, attributes, description, unit, kwds) = self.counter_queue.get()
            try:
                self._count(meter, counters, key, value, attributes, description, unit, **kwds)
            except Exception as e:
                log.exception(e)
            self.counter_queue.task_done()

    def _populate_attributes(self, attributes):
        attributes = dict(attributes)
        return attributes


def init_tracing(_from):
    """Initialize tracing libray.
    In our case, importing will initialize, and we simply send a started counter."""
    Tracer(__name__).count('init__' + _from)
