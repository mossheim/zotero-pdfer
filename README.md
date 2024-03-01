This is really slapdash script that watches a directory and tries to make PDFs out of any new HTML snapshots you put in Zotero and upload them to your library.

## Requirements

- fswatch command line utility : https://emcrisostomo.github.io/fswatch/usage.html
- python 3, with:
	- pyzotero - https://pyzotero.readthedocs.io/en/latest/#getting-started-short-version
	- weasyprint - https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation

## Usage

	./zotero-pdfer.py <storage-path> <api-id> <api-key> [<library-type>]

storage-path: the absolute path of the Zotero storage directory. For me that's `$HOME/Zotero/storage`.

api-id and api-key:
	1. Go to https://www.zotero.org/settings/keys .
	2. "Your userID for use in API calls is [numbers]" -> use that for api-id
	3. Click "create new private key" and make a key that has at least 'allow library access' and 'allow write access'. For groups I don't know what to do.

library-type: "user" or "group". Defaults to "user".

### Example usage on my machine

	./zotero-pdfer.py  /home/moss/Zotero/storage  19628390  0VnH8ZDXP7lR8huVHj3w1e1c  user

Might take a while to make or sync a pdf :(
