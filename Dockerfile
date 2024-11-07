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

# Adjustable ENV-vars
# LOG_LEVEL: Only for small part of code
ENV LOG_LEVEL=INFO
ENV LOG_LEVEL_MONITOR=INFO

# Hard-coded ENV-vars: Leave these unchanged
# for monitor_folder.py
ENV MONITOR_WATCH_DIR="/data/input"
ENV MONITOR_CACHE_DB_DIR="/data/cache"
# relative path should be like:
# DOSSIER_ID/database/whatsapp/DEVICE_ID/12345678/FILE
ENV MONITOR_FILTER_PATTERN_FILE='*/database/whatsapp/*/*/*'
# or for metadata json
# DOSSIER_ID/database/whatsapp/DEVICE_ID/12345678/metadata/FILE.json
ENV MONITOR_FILTER_PATTERN_METADATA='*/database/whatsapp/*/*/metadata/*'
# for whatsapp-extractor
ENV WHATSAPP_OUTPUT_ROOT="/data/output"

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
COPY monitor_folder.py main_wrapper.py main.py /app/bin/
COPY src /app/bin/src

WORKDIR /data

VOLUME ["/data/input", "/data/output", "/data/cache"]

# Use non-privileged user to run the app
USER appuser

CMD [ "python", "/app/bin/monitor_folder.py" ]