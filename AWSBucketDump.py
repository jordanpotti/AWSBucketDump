#!/usr/bin/env python

# AWSBucketDump is a tool to quickly enumerate AWS S3 buckets to look for loot.
# It's similar to a subdomain bruteforcer but is made specifically to S3
# buckets and also has some extra features that allow you to grep for
# delicous files as well as download interesting files if you're not
# afraid to quickly fill up your hard drive.

# by Jordan Potti
# @ok_bye_now

from argparse import ArgumentParser
import codecs
import requests
import xmltodict
import sys
import os
import shutil
from queue import Queue
from threading import Thread

q = Queue()
download_q = Queue()

grepList=None

MAX_SIZE=10000

def fetch(url):
    print('fetching ' + url)
    response = requests.get(url)
    if response.status_code == 403 or response.status_code == 404:
        status403(url)
    if response.status_code == 200:
        print(response.text)
        if "Content" in response.text:
            returnedList=status200(response,grepList,url)


def worker():
    while True:
        item = q.get()
        try:
            fetch(item)
        except Exception as e:
            print(e)
        q.task_done()

def downloadWorker():
    print('download worker running')
    while True:
        item = download_q.get()
        try:
            downloadFile(item)
        except Exception as e:
            print(e)
        download_q.task_done()

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


def print_banner():
         print('''\nDescription:
        AWSBucketDump is a tool to quickly enumerate AWS S3 buckets to look for loot.
        It's similar to a subdomain bruteforcer but is made specifically to S3
        buckets and also has some extra features that allow you to grep for
        delicous files as well as download interesting files if you're not
        afraid to quickly fill up your hard drive.

        by Jordan Potti
        @ok_bye_now'''
        )   

def main():
        parser = ArgumentParser()
        parser.add_argument("-D", dest="download", required=False, action="store_true", default=False, help="Download files. This requires significant diskspace") 
        parser.add_argument("-d", dest="savedir", required=False, default=False, help="if -D, then -d 1 to create save directories for each bucket with results.")
        parser.add_argument("-l", dest="hostlist", required=True, help="") 
        parser.add_argument("-g", dest="grepwords", required=False, help="Provide a wordlist to grep for")
        parser.add_argument("-m", dest="maxsize", required=False, default=1024, help="Maximum file size to download.")
        parser.add_argument("-t", dest="threads", type=int, required=False, default=1, help="thread count.")

        if len(sys.argv) == 1:
            print_banner()
            parser.error("No arguments given.")
            parser.print_usage
            sys.exit()

        
        # output parsed arguments into a usable object
        arguments = parser.parse_args()
        MAX_SIZE=arguments.maxsize

        # specify primary variables
        grepList = open(arguments.grepwords, "r")

        if arguments.download and arguments.savedir:
                print("Downloads enabled (-D), and save directories (-d) for each host will be created/used")
                #downloadFiles(arguments.maxsize, arguments.savedir)
                for i in range(1, arguments.threads):
                    t = Thread(target=downloadWorker)
                    t.daemon = True
                    t.start()

        elif arguments.download and not arguments.savedir:
                print("Downloads enabled (-D), and will be saved to current directory")
                #downloadFiles(arguments.maxsize)
                for i in range(1, arguments.threads):
                    t = Thread(target=downloadWorker)
                    t.daemon = True
                    t.start()
        else:
                print("Downloads were not enabled (-D), not saving results locally.")

        for i in range(0,arguments.threads):
            print('starting thread')
            t = Thread(target=worker)
            t.daemon = True
            t.start()
        
        with open(arguments.hostlist) as f:
                for line in f:
                        bucket = 'http://'+line.rstrip()+'.s3.amazonaws.com'
                        print('queuing {}'.format(bucket))
                        q.put(bucket)

        q.join()
        if arguments.download:
                download_q.join()

        cleanUp()

def cleanUp():
        print("Cleaning Up Files")
        
def status403(line):
    print(line.rstrip() + " is not accessible")

def status200(response,grepList,line):
    print("Pilfering "+line.rstrip())
    objects=xmltodict.parse(response.text)
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
        collectable = line+'/'+words
        if False and grepList != None and len(grepList) > 0:
            for grep_line in grepList:
                grep_line = (str(grep_line)).rstrip()
                if grep_line in words:
                        download_q.put(collectable)
                        print('Collectable: {}'.format(collectable))
                        break
        else:
            download_q.put(collectable)
            print('Collectable: {}'.format(collectable))
                

if __name__ == "__main__":
    main()

