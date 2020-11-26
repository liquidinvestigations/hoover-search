FROM python:3.8
ENV PYTHONUNBUFFERED 1

# merge

RUN set -e \
 && echo 'deb http://deb.debian.org/debian stable non-free' >> /etc/apt/sources.list \
 && echo 'deb http://deb.debian.org/debian stable-updates non-free' >> /etc/apt/sources.list \
 && echo 'deb http://security.debian.org stable/updates non-free' >> /etc/apt/sources.list \
 && apt-get update \
 && apt-get install -y gosu \
 && pip install pipenv

RUN mkdir -p /opt/hoover/search

ARG USER_NAME=liquid
ARG UID=666
ARG GID=666
RUN groupadd -g $GID -o $USER_NAME
RUN useradd -m -u $UID -g $GID -o -s /bin/bash $USER_NAME

WORKDIR /opt/hoover/search

ADD Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy --ignore-pipfile

COPY . .

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.3.0/wait /wait

ENV DJANGO_SETTINGS_MODULE hoover.site.settings.docker_local

RUN set -e \
 && SECRET_KEY=temp HOOVER_DB='postgresql://search:search@search-pg:5432/search' ./manage.py downloadassets \
 && SECRET_KEY=temp HOOVER_DB='postgresql://search:search@search-pg:5432/search' ./manage.py collectstatic --noinput \
 && chmod +x /wait

ENV USER_NAME $USER_NAME
ENV DATA_DIR /opt/hoover/search

RUN mkdir -p /opt/hoover/metrics
RUN chown $UID:$GID /opt/hoover/metrics


ENTRYPOINT ["/opt/hoover/search/docker-entrypoint.sh"]

CMD /opt/hoover/search/runserver
