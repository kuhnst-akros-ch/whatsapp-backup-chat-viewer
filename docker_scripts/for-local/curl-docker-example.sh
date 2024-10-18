#!/usr/bin/env bash

set -e

curl -X POST http://localhost:5000/whatsapp-backup-chat-viewer \
    -H "Content-Type: application/json" \
    -d '{
            "msgdb": "whatsapp_backup/databases/msgstore.db",
            "wadb": "whatsapp_backup/databases/wa.db",
            "backup_strategy": [
              "chats",
              "call_logs"
            ],
            "backup_output_style": "formatted_txt",
            "parsed_backup_output_dir": "output",
            "backup_specific_or_all_chat_call": [
              "all"
            ]
        }'
