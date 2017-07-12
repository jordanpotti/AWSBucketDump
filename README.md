# AWSBucketDump

 #### AWSBucketDump is a tool to quickly enumerate AWS S3 buckets to look for loot. It's similar to a subdomain bruteforcer but is made specifically for S3 buckets and also has some extra features that allow you to grep for delicious files as well as download interesting files if you're not afraid to quickly fill up your hard drive.
 #### @ok_bye_now

## Pre-Requisites
Non-Standard Python Libraries:

 xmltodict
 
 requests
 
 argparse

 Created with Python 3.6

## General

This is a tool that enumerates Amazon S3 buckets and looks for interesting files. 

I have example wordlists but I haven't put much time into refining them. 

https://github.com/danielmiessler/SecLists will have all the word lists you need. If you are targeting a specific company, you will likely want to use jhaddix's enumall tool which leverages recon-ng and Alt-DNS. 

https://github.com/jhaddix/domain && https://github.com/infosec-au/altdns

As far as word lists for grepping interesting files, that is completely up to you. The one I provided has some basics and yes, those word lists are based on files that I personally have found with this tool.

Using the download feature might fill your hard drive up, you can provide a max file size for each download at the command line when you run the tool. Keep in mind that it is in bytes.

I honestly don't know if Amazon rate limits this, I am guessing they do to some point but I haven't gotten around to figuring out what that limit is. If you want to add some threading features to this tool that would be neat..

After building this tool, I did find an interesting article from Rapid7 regarding this research: https://community.rapid7.com/community/infosec/blog/2013/03/27/1951-open-s3-buckets

## Usage:

 `python AWSBucketDump.py <hostlist> <grepWords> [-D] [Max File Size]`
