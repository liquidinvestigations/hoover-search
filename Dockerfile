FROM python:3.9
ENV PYTHONUNBUFFERED 1

RUN set -e \
 && echo 'deb http://deb.debian.org/debian stable non-free' >> /etc/apt/sources.list \
 && echo 'deb http://deb.debian.org/debian stable-updates non-free' >> /etc/apt/sources.list \
 && echo 'deb http://security.debian.org stable/updates non-free' >> /etc/apt/sources.list \
 && pip install pipenv \
 && mkdir -p /opt/hoover/search

WORKDIR /opt/hoover/search

ADD Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy --ignore-pipfile
RUN mkdir /opt/hoover/src && mv /opt/hoover/search/src/django-tus /opt/hoover/src/django-tus
ENV PYTHONPATH "${PYTHONPATH}:/opt/hoover/src/django-tus"
# global installs from git need a source folder
# https://pip.pypa.io/en/stable/topics/vcs-support/#editable-vcs-installs
# pipenv doesn't support the --src flag so we move the directory after it is created
COPY . .
COPY .git .


ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.3.0/wait /wait

ENV DJANGO_SETTINGS_MODULE hoover.site.settings.docker_local
ENV OTEL_TRACES_EXPORTER=none OTEL_METRICS_EXPORTER=none OTEL_LOGS_EXPORTER=none

RUN set -e \
 && SECRET_KEY=temp HOOVER_DB='postgresql://search:search@search-pg:5432/search' ./manage.py downloadassets \
 && SECRET_KEY=temp HOOVER_DB='postgresql://search:search@search-pg:5432/search' ./manage.py collectstatic --noinput \
 && chmod +x /wait

RUN git config --global --add safe.directory "*"

RUN apt-get update -y && \
        apt-get install -y pdftk &&  \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*

ENV GUNICORN_WORKER_CLASS=sync
ENV GUNICORN_WORKERS=2
ENV GUNICORN_THREADS=1
ENV GUNICORN_MAX_REQUESTS=1

CMD ./runserver
