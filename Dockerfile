# Builder Stage
FROM python:3-alpine AS builder

# user id of user www-data on Debian
ARG UID=33

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

ARG UID=33

# Adjustable ENV-vars
# LOG_LEVEL: Only for small part of code
ENV LOG_LEVEL=INFO
ENV LOG_LEVEL_MONITOR=INFO
ENV MONITOR_LOCK_FILENAME=Lock.lck
# OUTPUT_STYLE: 'output_style' or 'formatted_txt'
ENV OUTPUT_STYLE=formatted_txt
# Comma separated list, allowed values: 'call_logs', 'chats', 'contacts'
ENV CONVERSATION_TYPES=call_logs,chats,contacts

# Hard-coded ENV-vars: Leave these unchanged
# for monitor_folder.py
ENV MONITOR_WATCH_DIR="/data/input"
ENV MONITOR_CACHE_DB_DIR="/data/cache"
ENV OUTPUT_DIR=/data/output

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
COPY monitor_folder.py main.py /app/bin/
COPY src /app/bin/src

WORKDIR /data

VOLUME ["/data/input", "/data/output", "/data/cache"]

# Use non-privileged user to run the app
USER appuser

CMD [ "python", "/app/bin/monitor_folder.py" ]