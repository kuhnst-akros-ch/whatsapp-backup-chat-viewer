# Builder Stage
FROM python:3-alpine AS builder

ARG UID=10001

# Create a non-privileged user that the app will run under.
RUN adduser \
    --disabled-password \
    --gecos "" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Switch to the non-privileged user to run the application.
USER appuser

# Create a virtual environment and install Python packages as appuser
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=bind,source=requirements.txt,target=requirements.txt,readonly \
    python3 -m venv /home/appuser/venv && \
    /home/appuser/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    rm -rf /tmp/* /home/appuser/.cache/pip

# Application Stage (Final Image)
FROM python:3-alpine

ARG UID=10001

# Create a non-privileged user that the app will run under.
RUN adduser \
    --disabled-password \
    --gecos "" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Copy the virtual environment with correct ownership
COPY --from=builder /home/appuser/venv /app/venv

# Set environment variables
ENV PATH="/app/venv/bin:$PATH"

# copy to /app
COPY main.py /app/bin/
COPY src /app/bin/src

WORKDIR /data

CMD ["todo"]
