FROM python:3.13
# WORKDIR /app

RUN python -m venv /opt/venv

COPY pyproject.toml .
COPY /app /app
COPY README.md .
COPY .env .

RUN . /opt/venv/bin/activate && /opt/venv/bin/pip install --upgrade pip && /opt/venv/bin/pip install .
ENTRYPOINT ["/opt/venv/bin/python", "-m", "app.main"]
