
import requests
import xmltodict
import sys

from datetime import datetime

_timestr = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
timestr = _timestr.replace(":", "-")

if len(sys.argv) !=3:
	print("Usage: aws_enum.py wordlist grepwordlist")
	sys.exit(0)

grepList = open(sys.argv[2], "r")
interestingFiles = open('interestingFiles.txt','w+')
responseFile=open('responseFile.txt', "w+")
responseFile.close()
responseFile = open('responseFile.txt',"wb")

with open(sys.argv[1]) as f:
	for line in f:
		r = requests.get("http://"+line.rstrip() + ".s3.amazonaws.com")
		responseFile.write(r.content)
		if r.status_code == 403:
			break
		if r.status_code == 307:
			objects=xmltodict.parse(site)
			for Endpoint in objects['Error']:
				endpoint.append(Contents['Endpoint'])
				r = requests.get(endpoint)                    
				break        
		if r.status_code == 200:
			objects=xmltodict.parse(responseFile)
			for Contents in objects['ListBucketResult']['Contents']:
				Key.append(Contents['Key'])
				for lines in grepList:
					for words in Key:
						if words in line:
							interestingFiles.write(line+".s3.amazonaws.com/"+lines)
							break
			
			
			
