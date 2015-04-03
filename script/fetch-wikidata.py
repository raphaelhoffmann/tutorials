#!/usr/bin/env python3

from glob import glob
import queue
from queue import Queue
import os
import urllib
import urllib.request
import re
import json
import csv
import os.path

BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")
DATA_DIR = BASE_DIR + '/data'

def download_wikidata():
    DOWNLOAD_URL = ('http://dumps.wikimedia.org/other/wikidata/20150330.json.gz')
    ARCHIVE_FILENAME = 'dump.json.gz'
    data_path = os.path.join(DATA_DIR, "wikidata")
    archive_path = os.path.join(data_path, ARCHIVE_FILENAME)
    if os.path.exists(archive_path):
        print("skipping download, found %s" % archive_path) 
    else:
        """Download the dataset."""
        print("downloading %s" % DOWNLOAD_URL)
        print("into %s" % data_path)
        if not os.path.exists(data_path):
          os.makedirs(data_path)

        def progress(blocknum, bs, size):
            total_sz_mb = '%.2f MB' % (size / 1e6)
            current_sz_mb = '%.2f MB' % ((blocknum * bs) / 1e6)
            print('\rdownloaded %s / %s' % (current_sz_mb, total_sz_mb), end='')

        urllib.request.urlretrieve(DOWNLOAD_URL, filename=archive_path,
                                   reporthook=progress)
        print()



if __name__ == "__main__":
    download_wikidata()
