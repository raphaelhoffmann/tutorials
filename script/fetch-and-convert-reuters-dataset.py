#!/usr/bin/env python3

# The Reuters dataset is stored in SGML which we would like to parse with with Python's
# SGML parser. Python has stopped bundling SGML parser starting with Python 3.0, but one
# can convert the SGML parser from Python 2.7.9 using Python's 2to3 command line tool.
# We include a converted version in sgmllib.py.

from sgmllib import SGMLParser
from glob import glob
import queue
from queue import Queue
import os
import urllib
import urllib.request
import tarfile
import re
import json

def download_reuters(data_path=None):
    # note: this method is inspired by scikit
    DOWNLOAD_URL = ('http://archive.ics.uci.edu/ml/machine-learning-databases/'
                    'reuters21578-mld/reuters21578.tar.gz')
    ARCHIVE_FILENAME = 'reuters21578.tar.gz'
    if data_path is None:
        data_home = "."
        data_path = os.path.join(data_home, "reuters")
    if not os.path.exists(data_path):
        """Download the dataset."""
        print("downloading dataset (once and for all) into %s" %
              data_path)
        os.mkdir(data_path)

        def progress(blocknum, bs, size):
            total_sz_mb = '%.2f MB' % (size / 1e6)
            current_sz_mb = '%.2f MB' % ((blocknum * bs) / 1e6)
            print('\rdownloaded %s / %s' % (current_sz_mb, total_sz_mb), end='')

        archive_path = os.path.join(data_path, ARCHIVE_FILENAME)
        urllib.request.urlretrieve(DOWNLOAD_URL, filename=archive_path,
                                   reporthook=progress)
        print("untarring Reuters dataset...")
        tarfile.open(archive_path, 'r:gz').extractall(data_path)
        print("done.")


class ReutersParser(SGMLParser):
    q = queue.Queue()

    def __init__(self, verbose=0):
        SGMLParser.__init__(self, verbose)
        self.title = self.data = None
        self._reset()

    def _reset(self):
        self.in_title = 0
        self.in_body = 0
        self.in_topics = 0
        self.in_topic_d = 0
        self.title = ""
        self.body = ""
        self.topics = []
        self.topic_d = ""

    def handle_data(self, data):
        if self.in_body:
            self.body += data
        elif self.in_title:
            self.title += data
        elif self.in_topic_d:
            self.topic_d += data

    def start_reuters(self, attributes):
        pass

    def end_reuters(self):
        #self.body = re.sub(r'\s+', r' ', self.body)
        self.q.put({'title': self.title,
                          'body': self.body,
                          'topics': self.topics})
        self._reset()

    def start_title(self, attributes):
        self.in_title = 1

    def end_title(self):
        self.in_title = 0

    def start_body(self, attributes):
        self.in_body = 1

    def end_body(self):
        self.in_body = 0

    def start_topics(self, attributes):
        self.in_topics = 1

    def end_topics(self):
        self.in_topics = 0

    def start_d(self, attributes):
        self.in_topic_d = 1

    def end_d(self):
        self.in_topic_d = 0
        self.topics.append(self.topic_d)
        self.topic_d = ""

def stream_documents():
    data_path = "./reuters"
    for filename in glob(os.path.join(data_path, "*.sgm")):
        filehandle = open(filename, 'r', encoding='latin-1')
        parser = ReutersParser()
        while 1:
            sgmldata = filehandle.read(1024)
            if not sgmldata:
                break
            parser.feed(sgmldata)
            try:
                while 1:
                    yield parser.q.get_nowait()
            except queue.Empty:
                pass
        parser.close()       

if __name__ == "__main__":
    download_reuters()

    filehandle = open('./reuters/converted.txt', 'w', encoding='utf-8')
    for obj in stream_documents():
        obj_str = json.dumps(obj, sort_keys=True)
        print(obj_str, file=filehandle)
    filehandle.close()

