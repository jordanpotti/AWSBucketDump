#!/usr/bin/env python

# AWSBucketDump is a tool to quickly enumerate AWS S3 buckets to look for loot.
# It's similar to a subdomain bruteforcer but is made specifically to S3
# buckets and also has some extra features that allow you to grep for
# delicous files as well as download interesting files if you're not
# afraid to quickly fill up your hard drive.

# by Jordan Potti
# @ok_bye_now

import codecs
import requests
import xmltodict
import sys
import os
import shutil
from optparse import OptionParser
from queue import Queue
from threading import Thread

parser = OptionParser()
parser.add_option("-D", type="int", help="Enable Downloads and set size", dest="max_file_size", metavar="DOWNLOAD_SIZE", default=-1)
parser.add_option("-t", type="int", help="Threads", dest="thread_cnt", metavar="THREAD_COUNT", default=1)
(options, args) = parser.parse_args()

print(options)


print(args)


if len(args) <=1:
    print('''\nDescription:
    AWSBucketDump is a tool to quickly enumerate AWS S3 buckets to look for loot.
    It's similar to a subdomain bruteforcer but is made specifically to S3
    buckets and also has some extra features that allow you to grep for
    delicous files as well as download interesting files if you're not
    afraid to quickly fill up your hard drive.

    by Jordan Potti
    @ok_bye_now'''
    )
    print("\nUsage: \n       AWSBucketDump -D <DOWNLOAD_SIZE> -t THREAD_COUNT <wordlist> <grepwordlist>")
    print("       -D  <Max File Size in Bytes> -  Download Interesting Files")
    print("       Please be careful when using -D, it ")
    print("       can fill up your disk space quickly")
    print("       -t how many threads to run")
    print("\nExample:\n       python -D 10000000 -t 3 AWSBucketDump.py top1000.txt grepWords.txt")
    sys.exit(0)

masterList = open('masterList.txt','w+')
interestingFiles = open('interestingFiles.txt','w+')

q = Queue()
download_q = Queue()

def fetch(url):
    response = requests.get(url)
    if response.status_code == 403 or response.status_code == 404:
        status403(url)
    if response.status_code == 200:
        responseFile = open('responseFile.txt', 'wb')
        responseFile.truncate()
        responseFile.write(codecs.encode(response.text))
        responseFile.close()
        responseFile = open('responseFile.txt', 'r+')
        response = responseFile.read()
        if "Content" in response:
            responseFile.truncate()
            grepList = open(args[1], "r")
            returnedList=status200(response,grepList,url)
            for item in returnedList:
                interestingFiles.write(item)
                download_q.put(item)
            size=str(len(response))
            masterList.write('{} -------{}\n'.format(url, size))

def worker():
    while True:
        item = q.get()
        try:
            fetch(item)
        except Exception as e:
            print(e)
        q.task_done()

def downloadWorker():
    while True:
        item = download_q.get()
        try:
            downloadFile(item)
        except Exception as e:
            print(e)
        download_q.task_done()

def main():
    download = False
    if options.max_file_size >= 0:
        download = True
        print("You selected the download switch, I hope you have enough room")
        num_of_download_threads = options.thread_cnt
        for i in range(0,num_of_download_threads):
            t = Thread(target=downloadWorker)
            t.daemon = True
            t.start()

    num_of_threads = options.thread_cnt
    for i in range(0,num_of_threads):
        t = Thread(target=worker)
        t.daemon = True
        t.start()

    with open(args[0]) as f: # bucket names
        
        for line in f:
            q.put('http://'+line.strip()+'.s3.amazonaws.com')
       
    q.join()
    download_q.join()

def cleanUp():
    print("Cleaning Up Files")
    f = open("interestingFiles.txt")
    f2 = open("interestingFiles_Unique.txt", "w")
    uniquelines = set(f.read().split("\n"))
    f2.write("".join([line + "\n" for line in uniquelines]))
    f2.close()
    f.close()
    os.remove("interestingFiles.txt")
    os.remove("responseFile.txt")

def get_make_directory_return_filename_path(url):
    bits = url.split('/')
    directory = ''
    for i in range(2,len(bits)-1):
        directory = os.path.join(directory, bits[i])
    try:
        if not os.path.isdir(directory):
            os.makedirs(directory)
    except Exception as e:
        print(e)
    return os.path.join(directory, bits[-1]).rstrip()

def downloadFile(filename):
    MAX_SIZE = options.max_file_size
    print('Downloading {}'.format(filename))
    local_path = get_make_directory_return_filename_path(filename)
    local_filename = (filename.split('/')[-1]).rstrip()
    print('local {}'.format(local_path))
    if local_filename =="":
        print("Directory..\n")
    else:
        r = requests.get(filename.rstrip(), stream=True)
        if int(r.headers['Content-Length']) > MAX_SIZE:
            print("This file is greater than the specified max size.. skipping..\n")
        else:
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        r.close()


def status403(line):
    print(line.rstrip() + " is not accessible")

def status200(response,grepList,line):
    print("Pilfering "+line.rstrip())
    objects=xmltodict.parse(response)
    Keys = []
    interest=[]
    try:
        for child in objects['ListBucketResult']['Contents']:
            Keys.append(child['Key'])
    except:
        pass
    hit = False
    for words in Keys:
        words = (str(words)).rstrip()
        for grep_line in grepList:
            grep_line = (str(grep_line)).rstrip()
            if grep_line in words:
                    collectable = line+'/'+words
                    interest.append(collectable+"\n")
                    print('Collectable: {}'.format(collectable))
                    break
    return(interest)
                                                
if __name__ == '__main__':
    main()
