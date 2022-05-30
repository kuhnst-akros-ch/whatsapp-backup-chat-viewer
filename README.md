# Whatsapp Backup Chat Viewer

<!-- Add `badges` here-->

A Project to extract Whatsapp conversations from the app's SQLite database and exporting them as HTML or TXT files.

<!-- Add TXT Output -->

<!-- Add HTML Output -->

### Motivation

Recently I lost my phone and as any normal person, my whatsapp contained lots of data that I wasn't willing to let go and I had to find a way to get this data back. So I somehow (tbh not somehow, there are a lot of people who have shared how to fetch that) was able to get the whatsapp's SQLite database from my google backup. But having just the database doesn't help me much so I decided to create a parser for the database and export in chat format as HTML.

### Features

- Export the chats to txt files (one per chat).
<!-- - Export the chats to a WhatsApp Web like HTML page. -->

## Usage

### Prerequisites:

- [Whatsapp Database file](#retrieving-whatsapp-databases)
  - msgstore.db
  - wa.db

<!-- ### Quickstart:

- Run the following script:

```shell
$ python main.py --msgdb="path_to_msgstore.db" --wadb="path_to_wa.db" --output="txt_formatted"
``` -->

<!-- ## Retrieving WhatsApp Databases

For retrieving the WhatsApp database files from an Android device there are several options.

(This section will be updated soon.) -->

## License

This project is licensed under the [BSD-2-Clause License](./LICENSE.md)

## Disclaimer

This project is not endorsed or certified by WhatsApp Inc. and is meant for personal and educational purposes only. I don't take any responsibility for what you do with this program.
