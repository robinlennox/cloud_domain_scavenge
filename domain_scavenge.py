import os
import hashlib
import urllib2
import time
from datetime import date, timedelta
import re
from multiprocessing.dummy import Pool as ThreadPool

def main():
	global google_logo_md5

	#MD5 Google Default Logo
	google_logo_url='https://www.google.com/a/cpanel/images/logo.gif'
	response = urllib2.urlopen(google_logo_url)
	google_logo_md5=hashlib.md5(response.read()).hexdigest()

	today = date.today() - timedelta(days=1)
	yesterday = today.strftime('%Y/%m/%d')
	expired_domain_url="http://expire.biz/"+yesterday
	expired_domain_responce_list = get_html(expired_domain_url).split()
	# Make the Pool of workers
	pool = ThreadPool(20)
	results = pool.map(check_domain, expired_domain_responce_list)
	pool.close()
	pool.join()

def check_domain(target):
	google_message=check_google_app(target)
	if google_message:
		print "Found - "+google_message+target

def other_checks(target,message):
	number_of_screenshots=1
	web_archive_url="http://web.archive.org/cdx/search/cdx?url="+target+"&fl=timestamp&output=json&limit=100"
	search_response = get_html(web_archive_url)
	number_of_screenshots=search_response.count('\n')-number_of_screenshots
	if number_of_screenshots > 0:
		message="WayBackMachine found "+str(number_of_screenshots)+" screenshots, "+message

	duckduckgo_url="http://api.duckduckgo.com/?q="+target+"&format=json"
	search_response = get_html(duckduckgo_url)
	match=re.search(r'Results":\[\]',search_response)
	if not match:
		message="Result/s Found on DuckDuckGo, "+message

	return message

def check_google_app(target):
	check_doc_link="https://www.google.com/a/"+target+"/ServiceLogin?https://docs.google.com/a/"+target
	test_url_logo="https://www.google.com/a/cpanel/"+target+"/images/logo.gif"
	# Catch urllib2 Connection Loss and retry send for 10 Times
	i=0
	while  ( i < 40 ):
		try:
			adminreset="https://admin.google.com/"+target+"/VerifyAdminAccountPasswordReset"
			test_url_logo="https://www.google.com/a/cpanel/"+target+"/images/logo.gif"
			message=""
			# Catch urllib2 Connection Loss and retry send for 10 Times
			adminreset_response = urllib2.urlopen(adminreset)
			check_doc_link="https://www.google.com/a/"+target+"/ServiceLogin?https://docs.google.com/a/"+target
			doc_response = urllib2.urlopen(check_doc_link)
			if not "Server error" in doc_response.read():
				# Check if Other Info is available
				message=other_checks(target,message)
				message="Used Google Apps for Domain: "+message

			if not "Server error" in adminreset_response.read():
				#Check for Custom Logo
				logo_response = urllib2.urlopen(test_url_logo, timeout = 10)
				test_url_md5=hashlib.md5(logo_response.read()).hexdigest()
				if not google_logo_md5 == test_url_md5:
					message=message+"Custom Logo, "

			return message
			i=40 # Break Loop

		except:
			print "Retry Google App-"+target
			i=i+1
			time.sleep(5)

def get_html(url):
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36"')]
	response = opener.open(url)
	responce_string=response.read()
	return responce_string

if __name__ == "__main__":
	main()
