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
import traceback
import yara
import logging
from queue import Queue
from threading import Thread, Lock
from common import pretty_print, log

bucket_q = Queue()
download_q = Queue()

grep_list = None

arguments = None

yara_rules = None

#Disable requests logging
logging.getLogger("requests").setLevel(logging.WARNING)

def yara_index_build():
    with open('YaraRules/index.yar', 'w') as yar:
        for filename in os.listdir('YaraRules'):
            if filename.endswith('.yar') and filename != 'index.yar':
                include = 'include "{0}"\n'.format(filename)
                yar.write(include)

def fetch(url):
    log('Fetching ' + url + '...',logging.DEBUG)
    response = requests.get(url)
    if response.status_code == 403 or response.status_code == 404:
        status403(url)
    if response.status_code == 200:
        if "Content" in response.text:
            returnedList=status200(response,grep_list,yara_rules,url)


def bucket_worker():
    while True:
        item = bucket_q.get()
	print("Processing: {}".format(item))
        try:
            fetch(item)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            log(e,logging.ERROR)
        bucket_q.task_done()

def downloadWorker():
    log('Download worker running...',logging.DEBUG)
    while True:
        item = download_q.get()
        try:
            downloadFile(item)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            logging(e,logging.ERROR)
        download_q.task_done()

directory_lock = Lock()

def get_directory_lock():
    directory_lock.acquire()

def release_directory_lock():
    directory_lock.release()


def get_make_directory_return_filename_path(url):
    global arguments
    bits = url.split('/')
    directory = arguments.savedir
    for i in range(2,len(bits)-1):
        directory = os.path.join(directory, bits[i])
    try:
        get_directory_lock()
        if not os.path.isdir(directory):
            os.makedirs(directory)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        log(e,logging.ERROR)
    finally:
        release_directory_lock()

    return os.path.join(directory, bits[-1]).rstrip()

interesting_file_lock = Lock()
def get_interesting_file_lock():
    interesting_file_lock.acquire()

def release_interesting_file_lock():
    interesting_file_lock.release()


def write_interesting_file(filepath):
    try:
        get_interesting_file_lock()
        with open('interesting_file.txt', 'ab+') as interesting_file:
            interesting_file.write(filepath.encode('utf-8'))
            interesting_file.write('\n'.encode('utf-8'))
    finally:
        release_interesting_file_lock()
    


def downloadFile(filename):
    global arguments
    allowFileWrite = True
    log('Downloading: {}'.format(filename))
    local_path = get_make_directory_return_filename_path(filename)
    local_filename = (filename.split('/')[-1]).rstrip()
    log('Local File: {}'.format(local_path))
    if local_filename =="":
        log("Directory..\n",logging.DEBUG)
    else:
        r = requests.get(filename.rstrip(), stream=True)
        if 'Content-Length' in r.headers:
            if int(r.headers['Content-Length']) > arguments.maxsize:
                log("Content Length Exceeded: {} is greater than the specified max size. Skipped".format(filename))
            else:
                file_data = r.content
                if yara_rules != None:
                    matches = yara_rules.match(data=file_data)
                    #print(matches)
                    if len(matches) > 0:
                        for match in matches['main']:
                            #print str(match.rule)
                            log("Yara Rule Match: {} matched {}".format(filename,(match['rule'])))
                    else:
                        allowFileWrite = False
                if allowFileWrite == True:
                    with open(local_path, 'wb') as f:
                        f.write(file_data)
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


def cleanUp():
    log("Cleaning up files...",logging.DEBUG)

def status403(line):
    log("403 Error: "+line.rstrip() + " is not accessible.")


def queue_up_download(filepath):
    download_q.put(filepath)
    log('Collectable: {}'.format(filepath),logging.DEBUG)
    write_interesting_file(filepath)


def status200(response,grep_list,yara_rules,line):
    log("Pilfering "+line.rstrip() + '...',logging.DEBUG)
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
        if grep_list != None and len(grep_list) > 0:
            for grep_line in grep_list:
                grep_line = (str(grep_line)).rstrip()
                if grep_line in words:
                    queue_up_download(collectable)
                    break
        else:
            queue_up_download(collectable)

def main():
    global arguments
    global grep_list
    global yara_rules
    parser = ArgumentParser()
    parser.add_argument("-D", dest="download", required=False, action="store_true", default=False, help="Download files. This requires significant disk space.") 
    parser.add_argument("-d", dest="savedir", required=False, default='', help="If -D, then -d 1 to create save directories for each bucket with results.")
    parser.add_argument("-l", dest="hostlist", required=True, help="") 
    parser.add_argument("-g", dest="grepwords", required=False, help="Provide a wordlist to grep for.")
    parser.add_argument("-m", dest="maxsize", type=int, required=False, default=1024, help="Maximum file size to download.")
    parser.add_argument("-t", dest="threads", type=int, required=False, default=1, help="Number of threads.")
    parser.add_argument("-Y", dest="runyara", required=False, action="store_true", default=False,help="Run Yara rules against downloads and only save matches")
    if len(sys.argv) == 1:
        print_banner()
        parser.error("No arguments given.")
        parser.print_usage
        sys.exit()

    
    # output parsed arguments into a usable object
    arguments = parser.parse_args()

    if arguments.runyara != False:
        yara_index_build()
        yara_rules = yara.compile("YaraRules/index.yar")
    # specify primary variables
    if arguments.grepwords != None:
        with open(arguments.grepwords, "r") as grep_file:
            grep_content = grep_file.readlines()
        grep_list = [ g.strip() for g in grep_content ]

    if arguments.download and arguments.savedir:
        print("Downloads enabled (-D), save directories (-d) for each host will be created/used.")
        print("Default Download Directory: {}".format(arguments.savedir))
    elif arguments.download and not arguments.savedir:
        print("Downloads enabled (-D), will be saved to current directory.")
    else:
        print("Downloads were not enabled (-D), not saving results locally.")
    # start up bucket workers
    for i in range(0,arguments.threads):
        log('Starting thread...',logging.DEBUG)
        t = Thread(target=bucket_worker)
        t.daemon = True
        t.start()
       
    # start download workers 
    for i in range(1, arguments.threads):
        t = Thread(target=downloadWorker)
        t.daemon = True
        t.start()

    with open(arguments.hostlist) as f:
        for line in f:
            bucket = 'http://'+line.rstrip()+'.s3.amazonaws.com'
            log('Queuing: {}'.format(bucket))
            bucket_q.put(bucket)

    bucket_q.join()
    if arguments.download:
        download_q.join()

    cleanUp()

if __name__ == "__main__":
    main()

