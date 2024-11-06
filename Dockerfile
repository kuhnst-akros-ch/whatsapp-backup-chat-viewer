FROM python:3-alpine

# Create a non-privileged user that the app will run under.
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Switch to the non-privileged user to run the application.
USER appuser

WORKDIR /app

# Create a virtual environment
RUN python3 -m venv venv

# Ensure the virtual environment is used for all future commands
ENV PATH="/app/venv/bin:$PATH"

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/home/appuser/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt,readonly \
    --mount=type=bind,source=docker_scripts/docker-requirements.txt,target=docker-requirements.txt,readonly \
    python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -m pip install -r docker-requirements.txt \
    && rm -rf /tmp/*

# copy to /app
COPY \
    main.py \
    docker_scripts/docker_flask.py \
    /app/
COPY src /app/src

# Port for HTTP server
EXPOSE 5000

# Start the Flask app with Gunicorn in production mode
# workers in production should be: (2 cpu-cores * 2) + 1
# change timeout in both Dockerfile and nginx.conf !
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "5", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "docker_flask:app"]
