FROM python:3.12-alpine3.19

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Europe/Prague

RUN apk update && apk add gcc g++ musl-dev ffmpeg-dev git openjdk17-jdk openjdk17-jre libffi-dev
WORKDIR /morpheus
RUN mkdir -p /morpheus/logs

# Install python dependencies
RUN /usr/local/bin/python -m pip install --upgrade pip
COPY . .
RUN pip3 install -r requirements.txt

RUN git config --global --add safe.directory /morpheus

ENTRYPOINT [ "python3", "morpheus.py" ]
