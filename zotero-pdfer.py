#!/bin/env python
import subprocess
from pyzotero import zotero
import weasyprint
import glob
import os
import sys
import tempfile
import time

###################################

dir_to_watch = sys.argv[1]
api_id = sys.argv[2]
api_key = sys.argv[3]
lib_type = sys.argv[4] if len(sys.argv) == 5 else 'user'

def is_targeted_dir(ename):
	return all(c.isdigit() or c.isupper() for c in os.path.basename(ename))

def process_dir(fulldir):
    starttime = time.time()
    timeout = 3.0
    while time.time() - starttime < timeout:
        htmls = glob.glob(os.path.join(fulldir, '*.html'))
        if len(htmls) == 1:
            process_html(os.path.basename(fulldir), htmls[0])
            return
        time.sleep(0.1)
    print(f'-- WARNING: {fulldir} either had zero or more than one html file inside, skipping')

def process_html(ename, htmlpath):
	with tempfile.TemporaryDirectory() as tdir:
		pdfpath = os.path.join(tdir, os.path.basename(htmlpath) + ".pdf")
		print(f"-- Converting {htmlpath} to PDF -> {pdfpath}")
		wh = weasyprint.HTML(filename=htmlpath)
		wh.write_pdf(pdfpath)
		print(f"-- Wrote PDF to {pdfpath}")
		print(f"-- Trying to connect to zotero with api ID {api_id} and ename {ename}")
		zot = zotero.Zotero(api_id, lib_type, api_key)
		item = get_most_recent_zotero(zot, ename)
		if item is not None:
			attach_zotero_pdf(zot, item, pdfpath)

def run_fswatch_loop():
	args = ['fswatch', dir_to_watch, '--event', 'MovedTo']
	print(f'-- Running fswatch: {args}')
	with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0, encoding='utf-8') as proc:
		while True:
			print(f"-- Waiting for next task in {dir_to_watch}")
			ename = proc.stdout.readline().strip()
			if is_targeted_dir(ename):
				print(f"-- Found new directory {ename}, trying to convert html snapshot inside")
				process_dir(ename)
			else:
				print(f"-- INFO: event {ename} wasn't a targeted event")


def attach_zotero_pdf(zot, item_key, pdfpath):
	print(f"-- Uploading zotero pdf [{item_key}, {pdfpath}]")
	zot.attachment_simple([pdfpath], item_key)

def get_most_recent_zotero(zot, ename):
	print(f"-- Getting most recent zotero entry")
	starttime = time.time()
	timeout = 20.0
	while time.time() - starttime < timeout:
		items = zot.top(limit=5, sort='dateAdded', direction='desc')
		print(f"-- Checking top {len(items)} items")
		for item in items:
			if 'links' in item:
				if 'attachment' in item['links']:
					attachment = item['links']['attachment']
					if 'href' in attachment:
						if attachment['href'].endswith(ename):
							return item['key']
						else:
							print(f"-- INFO: {attachment['href']} doesn't end with {ename}")
					else:
						print(f"-- INFO: no href in {attachment}")
				else:
					print(f"-- INFO: no attachment in {item['links']}")
			else:
				print(f"-- INFO: no links in {item}")
		time.sleep(3.0)
	print(f'-- WARNING: {ename} had an issue with access, skipping')
	return None

run_fswatch_loop()
