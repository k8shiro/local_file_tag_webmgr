ARG PYTHON_VER

FROM python:${PYTHON_VER}

USER root

RUN mkdir src

WORKDIR src

COPY src/requirements.txt requirements.txt
RUN pip install -r requirements.txt

CMD ["gunicorn", "routes:app", "-k", "gevent", "-b", "0.0.0.0:80", "--log-level", "debug", "--workers", "4"]
