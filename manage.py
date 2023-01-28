#!/usr/bin/env python
import os
import sys

from hoover.search.tracing import Tracer, init_tracing

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hoover.site.settings")

    init_tracing('manage.py')
    tracer = Tracer('manage.py')

    from django.core.management import execute_from_command_line

    with tracer.span("-".join(['manage'] + sys.argv[1:2])) as span:
        span.set_attribute('cmdline.args', " ".join(sys.argv))
        execute_from_command_line(sys.argv)
