FROM python:3.12-slim-bookworm

ARG SANDBOX_USER_UID
ARG SANDBOX_DIR

RUN apt-get update && \
    apt-get -y install nano && \
    pip install --upgrade pip && \
    pip install pipenv

RUN apt-get -y install openjdk-17-jdk-headless

RUN adduser \
    --system \
    --gecos \
    --disabled-login \
    --disabled-password \
    --home ${SANDBOX_DIR} \
    --uid ${SANDBOX_USER_UID} \
    sandbox && \
    chown root:root ${SANDBOX_DIR}

COPY ./src/Pipfile ./src/Pipfile.lock /tmp/
RUN cd /tmp && pipenv install --deploy --dev --system

WORKDIR ${SANDBOX_DIR}
