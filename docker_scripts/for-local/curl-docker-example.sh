#!/usr/bin/env bash

set -e

curl -X POST http://localhost:5000/whatsapp-backup-chat-viewer \
    -H "Content-Type: application/json" \
    -d '{"mdb": "whatsapp_backup/databases/msgstore.db", "wdb": "whatsapp_backup/databases/wa.db", "output": "output"}'
