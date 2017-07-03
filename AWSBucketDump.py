#!/usr/bin/env python

# AWSBucketDump is a tool to quickly enumerate AWS S3 buckets to look for loot.
# It's similar to a subdomain bruteforcer but is made specifically to S3
# buckets and also has some extra features that allow you to grep for
# delicous files as well as download interesting files if you're not
# afraid to quickly fill up your hard drive.

# by Jordan Potti
# @okbyenow

import requests
import xmltodict
import sys
import os
import shutil

if len(sys.argv) <=2:
        print('''\nDescription:
        AWSBucketDump is a tool to quickly enumerate AWS S3 buckets to look for loot.
        It's similar to a subdomain bruteforcer but is made specifically to S3
        buckets and also has some extra features that allow you to grep for
        delicous files as well as download interesting files if you're not
        afraid to quickly fill up your hard drive.

        by Jordan Potti
        @okbyenow'''
        )
        print("\nUsage: \n       AWSBucketDump <wordlist> <grepwordlist> -D <Max File Size in Bytes>")
        print("       -D  <Max File Size in Bytes> -  Download Interesting Files")
        print("       Please be careful when using -D, it ")
        print("       can fill up your disk space quickly")
        print("\nExample:\n       python AWSBucketDump.py top1000.txt grepWords.txt -D 1000000000")
        sys.exit(0)
def main():
        try:
                download = False
                if '-D' in str(sys.argv):
                        download = True
                        print("You selected the download switch, I hope you have enough room")
                grepList = open(sys.argv[2], "r")
                masterList = open('masterList.txt','w+')
                interestingFiles = open('interestingFiles.txt','w+')
                responseFile=open('responseFile.txt', "w+")
                responseFile.close()
                responseFile = open('responseFile.txt',"wb")
                with open(sys.argv[1]) as f:
                        for line in f:
                                try:
                                        response = ''
                                        try:
                                                r = requests.get("http://"+line.rstrip() + ".s3.amazonaws.com")
                                        except:
                                                print("http://"+line.rstrip() + ".s3.amazonaws.com doesn't like us...moving on..\n")
                                                pass
                                        if r.status_code == 403 or r.status_code ==404:
                                                status403(line)
                                                

                                                
                                        if r.status_code == 200:
                                                responseFile.write(r.content)
                                                responseFile.close()
                                                responseFile = open('responseFile.txt','r+')
                                                response = responseFile.read()
                                                if "Content" in response:
                                                        responseFile.truncate()
                                                        returnedList=status200(response,grepList,line)
                                                        for item in returnedList:
                                                                interestingFiles.write(item)
                                                        size=str(len(r.content))
                                                        masterList.write("http://"+line.rstrip() + ".s3.amazonaws.com ----------- "+size +"\n")
                                        responseFile = open('responseFile.txt',"wb")
                                        grepList = open(sys.argv[2], "r")
                                except:
                                        print("Oh my goodness that was scary, we almost crashed.. good thing for lazy programmers that resort to try excepts to fix things..")
                interestingFiles.close()
                responseFile.close()
                masterList.close()
                cleanUp()
                if download == True:
                        downloadFiles()
        except:
                print("I'm not sure what just happened but lets shut this thing down, I'm sorry..")
                        
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
        
def downloadFiles():
        MAX_SIZE = int(sys.argv[4])
        print(MAX_SIZE)
        print("Beginning File Download, this may take some time..")
        with open("interestingFiles_Unique.txt", "r") as fileList:
                for line in fileList:
                        if "http" not in line:
                                print("")
                        else:
                                print(line)
                                local_filename = (line.split('/')[-1]).rstrip()
                                r = requests.get(line.rstrip(), stream=True)
                                if int(r.headers['Content-Length']) > MAX_SIZE:
                                        print("This file is greater than the specified max size.. skipping..\n")
                                else:
                                        with open(local_filename, 'wb') as f:
                                                shutil.copyfileobj(r.raw, f)
                                r.close()
        
                
                

def status403(line):
        print("http://"+line.rstrip() + ".s3.amazonaws.com is not accessible")
                
def status200(response,grepList,line):

        print("Pilfering http://"+line.rstrip()+".s3.amazonaws.com/")
        objects=xmltodict.parse(response)
        Keys = []
        interest=[]
        try:
                for child in objects['ListBucketResult']['Contents']:
                        Keys.append(child['Key'])
        except:
               pass
        for lines in grepList:
                lines = (str(lines)).rstrip()
                for words in Keys:
                        words = (str(words)).rstrip()
                        if lines in words:
                                interest.append("http://"+line.rstrip()+".s3.amazonaws.com/"+words+"\n")
        return(interest)
                                                
main()                  
