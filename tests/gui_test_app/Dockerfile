FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:0 \
    GUI_TEST_APP_GEOMETRY=1280x800 \
    GUI_TEST_APP_DEPTH=24 \
    GUI_TEST_APP_READY_FILE=/tmp/gui-test-app-ready.json \
    GUI_TEST_APP_TIMEOUT=0 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-tk \
        tigervnc-standalone-server \
        x11-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

COPY docker-entrypoint.sh /usr/local/bin/gui-test-app-entrypoint

EXPOSE 5900 6000

ENTRYPOINT ["gui-test-app-entrypoint"]
CMD ["gui-test-app"]
