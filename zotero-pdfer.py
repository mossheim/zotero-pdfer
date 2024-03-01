#!/bin/env python
from inotify_simple import INotify, flags
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

def is_targeted_dir(event):
    _, emask, _, ename = event
    if emask & flags.ISDIR:
        if all(c.isdigit() or c.isupper() for c in ename):
            return True
    return False

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
        zot = zotero.Zotero(api_id, 'user', api_key)
        item = get_most_recent_zotero(zot, ename)
        attach_zotero_pdf(zot, item, pdfpath)

def run_inotify_loop():
    i = INotify()
    iflags = flags.MOVED_TO
    while True:
        print(f"-- Waiting for next task in {dir_to_watch}")
        wd = i.add_watch(dir_to_watch, iflags)
        for event in i.read():
            if is_targeted_dir(event):
                print(f"-- Found new directory {event.name}, trying to convert html snapshot inside")
                process_dir(os.path.join(dir_to_watch, event.name))
            else:
                print(f"-- INFO: event {event} wasn't a targeted event")


def attach_zotero_pdf(zot, item_key, pdfpath):
    print(f"-- Uploading zotero pdf [{item_key}, {pdfpath}]")
    zot.attachment_simple([pdfpath], item_key)

def get_most_recent_zotero(zot, ename):
    print(f"-- Getting most recent zotero entry")
    starttime = time.time()
    timeout = 20.0
    while time.time() - starttime < timeout:
        items = zot.top(limit=1, sort='dateAdded', direction='desc')
        print(f"-- Items: {items}")
        if len(items) > 0:
            if 'links' in items[0]:
                if 'attachment' in items[0]['links']:
                    attachment = items[0]['links']['attachment']
                    if 'href' in attachment:
                        if attachment['href'].endswith(ename):
                            return items[0]['key']
                        else:
                            print(f"-- WARNING: {attachment['href']} doesn't end with {ename}")
                    else:
                        print(f"-- WARNING: no href in {attachment}")
                else:
                    print(f"-- WARNING: no attachment in {items[0]['links']}")
            else:
                print(f"-- WARNING: no links in {items[0]}")
        else:
            print(f"-- WARNING: no items")
        time.sleep(2.0)
    print(f'-- WARNING: {ename} had an issue with access, skipping')

run_inotify_loop()
