import os
import logging
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Get the container's hostname to identify the replica
hostname = os.getenv('HOSTNAME', 'unknown')

# Enable logging for successful requests
if not app.debug:
	gunicorn_error_logger = logging.getLogger("gunicorn.error")
	app.logger.handlers = gunicorn_error_logger.handlers
	app.logger.setLevel(logging.INFO)

@app.route('/whatsapp-backup-chat-viewer', methods=['POST'])
def run_script():
	app.logger.info(f'{hostname} is processing request for /whatsapp-backup-chat-viewer with payload {request.json}')

	if not all([request.json.get('msgdb'), request.json.get('wadb'), request.json.get('parsed_backup_output_dir')]):
		return jsonify({"error": "Missing required parameters"}), 400

	# Call the script with the provided paths
	command = [
		"python", "main.py",
		"--msgdb", request.json.get('msgdb'),
		"--wadb", request.json.get('wadb'),
		"--backup_strategy", request.json.get('backup_strategy', 'both'),
		"--backup_output_style", request.json.get('backup_output_style', 'raw_txt'),
		"--parsed_backup_output_dir", request.json.get('parsed_backup_output_dir')
	]
	for backup_specific_or_all_chat_call in request.json.get('backup_specific_or_all_chat_call', ['all']):
		command.append("--backup_specific_or_all_chat_call")
		command.append(backup_specific_or_all_chat_call)

	result = subprocess.run(command, capture_output=True, text=True)

	if result.returncode != 0:
		return jsonify({"error": result.stderr}), 500

	app.logger.info(f'{hostname} finished processing request for /whatsapp-backup-chat-viewer with payload {request.json}')

	return jsonify({"message": "Script triggered successfully!", "output": result.stdout})

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
