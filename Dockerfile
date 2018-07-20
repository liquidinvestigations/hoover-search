FROM python:3
ENV PYTHONUNBUFFERED 1

RUN set -e \
 && echo 'deb http://deb.debian.org/debian jessie non-free' >> /etc/apt/sources.list \
 && echo 'deb http://deb.debian.org/debian jessie-updates non-free' >> /etc/apt/sources.list \
 && echo 'deb http://security.debian.org jessie/updates non-free' >> /etc/apt/sources.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends qrencode \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/hoover/search
WORKDIR /opt/hoover/search

ADD requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

RUN set -e \
 && echo 'SECRET_KEY="a"' > hoover/site/settings/local.py \
 && ./manage.py downloadassets \
 && ./manage.py collectstatic --noinput \
 && rm hoover/site/settings/local.py

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.3.0/wait /wait

RUN set -e \
 && echo '#!/bin/bash -e' > /runserver \
 && echo 'waitress-serve --port 80 hoover.site.wsgi:application' >> /runserver \
 && chmod +x /runserver /wait

CMD /wait && /runserver
