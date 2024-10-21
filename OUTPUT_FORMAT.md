Output Format
=============

# Target folders

The target folder is set by the `output_dir` parameter, typically set to `output`.

With value `output` these subfolders to `./output` will be created:
- call_logs: data of calls
- chats: data of chats
```
./output
|- call_logs
|- chats
```

The output described below is also in file form in `./example_output`.


# Contact format

A file './output/contacts.txt' is created containing all Whatsapp contacts in long format.

**Not all participants of chats and calls are in those contacts!**

Contacts are printed in 2 formats:

Short format:
- Name and number present: '{name} ({number})'
- number present: '{number}'
- contact not in Whatsapp contacts: '{jid}'

Long format with jid always included:
- Name and number present: '{name} ({number}, {jid})'
- number present: '{number} ({jid})'
- contact not in Whatsapp contacts: '{jid}'

## JID

`jid` example: `41763349999@s.whatsapp.net.txt`.

Format: '{number}@text'

Very often the number part is a phone number, but not always.

And the jid is not unique, there are Whatsapp contacts with the same jid.
It's probably the same person and often the number just differs in the country code (0041 vs +41).
Or the Whatsapp contact switched phone numbers.

# Call data format

A file in './output/call_logs' is created for all calls to or from a Whatsapp contact.

Example file structure:
```
./output
|- call_logs
    |- 41445209999@s.whatsapp.net.txt
    |- Firstname Lastname (+41786319999).txt
```

The first line contains the call participant (not the phone owner) followed by an empty line.

With parameter `output_style` set to `formatted_txt` (default), the file contents would be like:

File `41445209999@s.whatsapp.net.txt` (last call was a video call):
```
41445209999@s.whatsapp.net.txt

[2020-04-30 09:19:14]: Me ----> 41445209999@s.whatsapp.net.txt
	>>> Call Type: 📞 - Voice Call
	>>> Duration: 22 seconds
	>>> Status: 5
[2020-04-30 09:27:12]: 41445209999@s.whatsapp.net.txt ----> Me
	>>> Call Type: 📞 - Voice Call
	>>> Duration: 00 seconds
	>>> Status: 2
[2020-04-30 09:58:12]: Me ----> 41445209999@s.whatsapp.net.txt
	>>> Call Type: 📞 - Voice Call
	>>> Duration: 08:28 minutes
	>>> Status: 5
[2020-05-30 15:28:36]: 41445209999@s.whatsapp.net.txt ----> Me
	>>> Call Type: 📹 - Video Call
	>>> Duration: 04:06 minutes
	>>> Status: 5
```

File `Firstname Lastname (+41786319999).txt`:
```
Firstname Lastname (+41786319999, 971544759999@s.whatsapp.net)

[2019-01-18 11:30:10]: Me ----> Firstname Lastname (+41786319999)
	>>> Call Type: 📞 - Voice Call
	>>> Duration: 00 seconds
	>>> Status: 2
[2019-01-18 11:31:04]: Firstname Lastname (+41786319999) ----> Me
	>>> Call Type: 📞 - Voice Call
	>>> Duration: 05:08 minutes
	>>> Status: 5
```


# Chat data format

A file in './output/chats' is created for each chat with a Whatsapp contact or a chat group.

Example file structure:
```
./output
|- chats
    |- 41445209999@s.whatsapp.net.txt
    |- Firstname Lastname (+41786319999).txt
    |- Group-Name.txt
```

- For group chats: The first line contains the group name followed by all chat-group participants and an empty line
- For non-group chats: The first line contains the call participant (not the phone owner) followed by an empty line.

With parameter `output_style` set to `formatted_txt` (default), the file contents would be like:

File `41445209999@s.whatsapp.net.txt`:
```
41445209999@s.whatsapp.net.txt

[2024-05-03 20:10:36.077000] 'Change in the chat settings'
```

File `Firstname Lastname (+41786319999).txt`:
```
Firstname Lastname (+41786319999, 971544759999@s.whatsapp.net)

[2024-05-03 20:10:36.077000] 'Change in the chat settings'
[2024-05-03 20:10:36.095000] 'Change in the chat settings'
[2024-05-03 20:10:35.826000]: Firstname Lastname (+41786319999) - Hello! 😃 I’m at home 😉
[2024-05-03 20:10:50.505000]: Firstname Lastname (+41786319999)
	>>> Location: (45.702416015625,11.406912254333496)
[2024-05-08 08:31:29.258000]: Me - Look at my picture
	>>> Media: Media/WhatsApp Images/Sent/IMG-20240508-WA0000.jpg
[2024-05-09 11:49:57.446000]: Me - This message has 3 lines
Line 2
Line 3
[2024-05-09 11:50:12.855000]: Firstname Lastname (+41786319999) - Useful information
	>>> Reply to: Me - This message has 3 lines Line 2 Line 3
[2024-05-09 17:12:10.944000]: Firstname Lastname (+41786319999) - I’m waiting for you!
	>>> Reply to: 'Message has been deleted'
```

File `Group-Name.txt`:
```
Group-Name
41787868888@s.whatsapp.net
41797059999@s.whatsapp.net
Firstname Lastname (+41786319999, 971544759999@s.whatsapp.net)

[2020-02-07 12:57:09.272000] 'Change in the chat settings'
[2020-02-07 12:57:09.313000]: Me - Group-Name
[2020-02-07 12:57:09.333000] 'Change in the chat settings'
[2020-02-07 12:57:09.399000]: Me - 1581080239
[2020-02-07 12:57:14.524000]: Firstname Lastname (+41786319999) - Hello everyone
See you soon!
[2020-02-07 14:01:07.062000]: 41787868888@s.whatsapp.net - Looking forward to it 🤗🤗😘
[2020-02-07 14:09:06.892000]: 41787868888@s.whatsapp.net
	>>> Media: Media/WhatsApp Voice Notes/202006/PTT-20200207-WA0000.opus
[2020-02-08 05:59:06.233000] 'Change in the chat settings'
```


# TODO

- call_logs: Add information about `Me`. Phone number and name
- chats: Add information about all participants of a chat at the begginning of each file. Phone number and name