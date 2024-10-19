#!/usr/bin/env bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
IMG_NAME=whatsapp-backup-chat-viewer

docker build -t $IMG_NAME:latest "$SCRIPT_DIR/../.."

# MSYS_NO_PATHCONV prevents path fubar by git-bash on windows
MSYS_NO_PATHCONV=1 docker run -d \
  -p 5000:5000 \
  -v "$SCRIPT_DIR/../../whatsapp_backup:/app/whatsapp_backup" \
  -v "$SCRIPT_DIR/../../output:/app/output" \
  $IMG_NAME:latest