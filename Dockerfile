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
    python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && rm -rf /tmp/*

# copy to /app
COPY main.py /app/
COPY src /app/src

CMD ["todo"]
