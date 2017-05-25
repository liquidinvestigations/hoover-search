FROM python:3
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /opt/hoover/search
WORKDIR /opt/hoover/search

ADD requirements.txt /opt/hoover/search/
RUN pip install -r requirements.txt

ADD . /opt/hoover/search/
