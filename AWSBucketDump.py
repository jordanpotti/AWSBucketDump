#!/usr/bin/env python

# AWSBucketDump is a tool to quickly enumerate AWS S3 buckets to look for loot.
# It's similar to a subdomain bruteforcer but is made specifically to S3
# buckets and also has some extra features that allow you to grep for
# delicous files as well as download interesting files if you're not
# afraid to quickly fill up your hard drive.

# by Jordan Potti
# @ok_bye_now

import requests
import xmltodict
import sys
import os
import shutil
from argparse import ArgumentParser

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
        parser.add_argument("-m", dest="maxsize", required=False, help="Maximum file size to download.")

        if len(sys.argv) == 1:
            print_banner()
            parser.error("No arguments given.")
            parser.print_usage
            sys.exit()
        
        # output parsed arguments into a usable object
        arguments = parser.parse_args()

        # specify primary variables
        grepList = open(arguments.grepwords, "r")
        masterList = open('masterList.txt','w+')
        interestingFiles = open('interestingFiles.txt','w+')

        responseFile=open('responseFile.txt', "w+")
        responseFile.close()
        responseFile = open('responseFile.txt',"wb")
        
        with open(arguments.hostlist) as f:
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
                        except:
                                print("We almost crashed.. ")
        interestingFiles.close()
        responseFile.close()
        masterList.close()
        cleanUp()
        if arguments.download and arguments.savedir:
                print("Downloads enabled (-D), and save directories (-d) for each host will be created/used")
                downloadFiles(arguments.maxsize, arguments.savedir)
        elif arguments.download and not arguments.savedir:
                print("Downloads enabled (-D), and will be saved to current directory")
                downloadFiles(arguments.maxsize)
        else:
                print("Downloads were not enabled (-D), not saving results locally.")

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
        
def downloadFiles(maxsize, mkdir = False):
        MAX_SIZE = int(maxsize)
        print(MAX_SIZE)
        print("Beginning File Download, this may take some time..")
        i = 0
        with open("interestingFiles_Unique.txt", "r") as fileList:
                for line in fileList:
                        if "http" not in line:
                                print("")
                        else:
                                print(line)
                                local_filename = (line.split('/')[-1]).rstrip()
                                if local_filename =="":
                                        print("Directory..\n")
                                else:
                                        if mkdir:
                                                local_savedir = (line.split('/')[-2]).rstrip()
                                                # assign new path + filename for result for use in save below
                                                local_filename = "".join("./%s/%s") % (local_savedir, local_filename)
                                                # check if dir for host exists, if not create it
                                                if not os.path.exists("./%s" % local_savedir):
                                                        print("Creating directory for host: (%s)" % local_savedir)
                                                        os.mkdir(local_savedir)
                                                else:
                                                        print("Using existing directory for host: (%s)" % local_savedir)

                                                print("Saving file to: %s" % local_filename)


                                        r = requests.get(line.rstrip(), stream=True)
                                        if int(r.headers['Content-Length']) > MAX_SIZE:
                                                print("This file is greater than the specified max size.. skipping..\n")
                                        else:
                                                with open(local_filename, 'wb') as f:
                                                        shutil.copyfileobj(r.raw, f)
                                                        i = i+1
                                r.close()
        print(str(i) + " Files Downloaded\n")
                

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
        # make greplist optional, save everything if not supplied
        for lines in grepList:
            lines = (str(lines)).rstrip()
            for words in Keys:
                words = (str(words)).rstrip()
                if lines in words:
                    s = requests.get("http://"+line.rstrip()+".s3.amazonaws.com/"+words)
                if s.status_code != 200:
                    print("Received %s on %s" % (s.status_code, words))
                else:
                    interest.append("http://"+line.rstrip()+".s3.amazonaws.com/"+words+"\n")
                s.close()

        return(interest)
if __name__ == "__main__":
    main()                  
