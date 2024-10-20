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

	if not all([request.json.get('msgdb'), request.json.get('wadb'), request.json.get('output_dir')]):
		return jsonify({"error": "Missing required parameters"}), 400

	# Call the script with the provided paths
	command = [
	  "python", "main.py",
	  "--msgdb", request.json.get('msgdb'),
	  "--wadb", request.json.get('wadb'),
	  "--output_style", request.json.get('output_style', 'formatted_txt'),
	  "--output_dir", request.json.get('output_dir'),
	  "--conversation_types"
	] + request.json.get('conversation_types', ['call_logs', 'chats'], 'contacts')

	# Add phone_number_filter if provided
	phone_number_filters = request.json.get('phone_number_filter', [])
	if phone_number_filters:
		command.append("--phone_number_filter")
		command += phone_number_filters

	result = subprocess.run(command, capture_output=True, text=True)

	if result.returncode != 0:
		return jsonify({"error": result.stderr}), 500

	app.logger.info(f'{hostname} finished processing request for /whatsapp-backup-chat-viewer with payload {request.json}')

	return jsonify({"message": "Script triggered successfully!", "output": result.stdout})

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
