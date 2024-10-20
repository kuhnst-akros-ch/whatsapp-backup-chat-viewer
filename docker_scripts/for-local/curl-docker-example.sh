#!/usr/bin/env bash

set -e

curl -X POST http://localhost:5000/whatsapp-backup-chat-viewer \
    -H "Content-Type: application/json" \
    -d '{
            "msgdb": "whatsapp_backup/databases/msgstore.db",
            "wadb": "whatsapp_backup/databases/wa.db",
            "conversation_types": [
              "chats",
              "call_logs"
            ],
            "output_style": "formatted_txt",
            "output_dir": "output",
            "phone_number_filter": []
        }'
