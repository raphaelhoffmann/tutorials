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
import re
import json
import csv
import os.path

BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")
DATA_DIR = BASE_DIR + '/data'

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
        self.id = ""
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
        for name, value in attributes:
            if name.lower() == "newid":
                self.id = value

    def end_reuters(self):
        #self.body = re.sub(r'\s+', r' ', self.body)
        self.q.put({'id': self.id, 
                    'title': self.title,
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
    data_path = DATA_DIR + "/reuters"
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

def sgml_to_json():
    print("parsing sgml and converting to json")
    out_path = DATA_DIR + '/reuters/converted.txt'
    filehandle = open(out_path, 'w', encoding='utf-8')
    for obj in stream_documents():
        obj_str = json.dumps(obj, sort_keys=True)
        print(obj_str, file=filehandle)
    filehandle.close()
    print("saved output as %s" % out_path)

def json_to_csv():
    print("converting to csv")
    in_path = DATA_DIR + '/reuters/converted.txt'
    out_path = DATA_DIR + '/reuters/converted.csv'

    with open(in_path, 'r', encoding='utf-8') as jsonin, open(out_path, 'w', encoding='utf-8') as tsvout:
        tsvout = csv.writer(tsvout)
        for line in jsonin:
            obj = json.loads(line)
            tsvout.writerow([obj['id'], obj['body'], obj['title']])
    print("saved output as %s" % out_path)


if __name__ == "__main__":
    sgml_to_json()
    json_to_csv()
