How-To run `whatsapp-backup-chat-viewer` in Docker
==================================================

# Initial data

Place the files extracted from phones in a folder named `whatsapp_backup` in the root of this project.
This folder will be shared with Docker containers.

These files should be present:
- whatsapp_backup/databases/msgstore.db
- whatsapp_backup/databases/wa.db


# Build and run

Build an image and run it with:
```commandline
./docker_scripts/for-local/docker-build-run.sh
```

or simply use docker-compose with:
```commandline
docker-compose up -d
```


# Extract data

Run the sample script:
```commandline
./docker_scripts/for-local/curl-docker-example.sh
```
It uses curl to send a HTTP-POST request to the docker images.
The mentioned file paths are in the payload of the request.

Extracted data will be placed in the `output` folder, wich is also shared with Docker images.


## Parallel extraction

The DB files and the output path are parameters and can be individual per request.


## Stack inside the Docker image

The stack consists of:
- Gunicorn as the WSGI server
- Flask as the web framework handling HTTP requests
- and the Python script `main.py` providing the core logic

Gunicorn and Flask allow the script to run continuously, handling multiple HTTP requests concurrently, making it 
suitable for a web service, unlike running the `main.py` once and exiting.