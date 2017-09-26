FROM python:3
ENV PYTHONUNBUFFERED 1

RUN echo 'deb http://deb.debian.org/debian jessie non-free' >> /etc/apt/sources.list
RUN echo 'deb http://deb.debian.org/debian jessie-updates non-free' >> /etc/apt/sources.list
RUN echo 'deb http://security.debian.org jessie/updates non-free' >> /etc/apt/sources.list

RUN apt-get update
RUN apt-get install -y --no-install-recommends qrencode
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/hoover/search
WORKDIR /opt/hoover/search

ADD requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

RUN echo 'SECRET_KEY="a"' > hoover/site/settings/local.py
RUN ./manage.py downloadassets
RUN ./manage.py collectstatic --noinput
RUN rm hoover/site/settings/local.py

CMD waitress-serve --port 80 hoover.site.wsgi:application
