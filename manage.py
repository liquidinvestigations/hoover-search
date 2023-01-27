#!/usr/bin/env python
import os
import sys

import uptrace
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hoover.site.settings")

    if os.getenv('UPTRACE_DSN'):
        uptrace.configure_opentelemetry(
            service_name="hoover-search",
            service_version="0.0.0",
        )
        LoggingInstrumentor().instrument(set_logging_format=True)
        Psycopg2Instrumentor().instrument(skip_dep_check=True)
        DjangoInstrumentor().instrument()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
