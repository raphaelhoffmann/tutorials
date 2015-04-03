#!/usr/bin/env python3

from glob import glob
import queue
from queue import Queue
import os
import urllib
import urllib.request
import tarfile
import re
import os.path

BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")
DATA_DIR = BASE_DIR + '/data'

def download_reuters():
    DOWNLOAD_URL = ('http://archive.ics.uci.edu/ml/machine-learning-databases/'
                    'reuters21578-mld/reuters21578.tar.gz')
    ARCHIVE_FILENAME = 'reuters21578.tar.gz'
    data_path = os.path.join(DATA_DIR, "reuters")
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
        tarfile.open(archive_path, 'r:gz').extractall(data_path)
        print()


if __name__ == "__main__":
    download_reuters()
