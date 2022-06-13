from operator import index
import random
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import re
import os
import json
import html
from bs4 import BeautifulSoup
import random
import time
import logging
import traceback
import uuid
import datetime
#from os import access
#import numpy as np
# import pandas as pd
import boto3
from botocore.exceptions import ClientError
import io
from tqdm import tqdm
import shutil

from aws import AwsGateway


"""
import threading

# any exception should turn this on to quit all threads
threading_exit_flag = 0
browser_pool_limit = 10
browser_pool = []

# global function to get webpage source
def get_web_page_source(threadId, url, filename):
	if threading_exit_flag:
		exit()

	# create a new browser and return the page source
	if threadId>len(browser_pool):
		# create instance
		pass
	else:
		browser = browser_pool[threadId]

	# save file
	# ...
	pass

def clean_up_browser_pool():
	for browser in browser_pool:
		browser.close();
		browser.quit(); 
	browser_pool = []

# class to create thread
class BrowserThread (threading.Thread):
	def __init__(self, threadID, url, filename):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.url = url
		self.filename = filename

	def run(self):
		print ("Starting THREAD#" + str(self.threadID))
		get_web_page_source(self.threadID, self.url, self.filename)
		print ("Exiting THREAD#" + str(self.threadID))
"""



class ExtractorPage:
	"""ExtractorPage is class to handle extracting page source for a url

	Attributes:
		config (dictionary): Site settings
		page_name (str): Name of the page read from definition
		page_url (str): URL of the page read from definition
		page_checking (list): String list to find in page source to validate the page 
		page_url_refer_table (str): URL variables refer to which table
		page_url_cache_filename (str): Save captured data to this filename
		parsers (list): definition to get what infomation from page
		page_state (dictionary): Memory storage to store captured information
		pager_parser (dictionary): Information parsing rules for pager of URL
		wait_parsing_list (list): Queue to store parsing tasks
		page_retry (dictionary): Count of retrying for different URL

	"""

	config: None
	page_name: str
	page_url: str
	page_checking = []
	page_url_refer_table: str
	page_url_cache_filename: str
	parsers = []                   
	page_state = {}
	pager_parser = {}
	wait_parsing_list = []        
	page_retry = {}
	
	def __init__(self, definition, config):
		"""Constructor of ExractorPage

		Note:
		Store the site configs and save settings for parsing to attributes

		Args:
		definition (dictionary): page definition for extracting 
		config (dictionary): site setting definition 
		"""
		self.config = config

		self.page_name = definition["NAME"]
		self.page_url = definition["URL"]

		if "URL_CACHE_FILENAME" in definition:
			self.page_url_cache_filename = definition["URL_CACHE_FILENAME"]

		if "URL_REFER_TABLE" in definition:
			self.page_url_refer_table = definition["URL_REFER_TABLE"]

		self.page_checking = definition["CHECK"]

		if "PARSER" in definition:
			self.parsers = definition["PARSER"]

		if "PAGER_PARSER" in definition:
			self.pager_parser = definition["PAGER_PARSER"]


	def get_page_state(self):
		""" Fuction to get page state

		Note:
		May change to @property
		"""
		return self.page_state


	def _merge_url(self):
		"""Function to generate all possible URLs to access

		Note:
		Private function for class internal use only
		$_${} is the preserve tag for variables in URL

		Returns:
		List of three values: url, name and param
		url is the actual url to access
		name is for creating filename to store the source code 
		param is the value to substitute to regular expression to parse data
		"""
		fields_in_url = re.findall(r'\$_\${(\d+)}', self.page_url, re.M|re.I|re.S)

		# no merge is needed, return the original url
		if(len(fields_in_url)==0):
			return [ [self.page_url, self.page_name, []] ];

		refer_table = self.page_state[self.page_url_refer_table]

		vals_in_name = re.findall(r'\$_\${(\d+)}', self.page_url_cache_filename, re.M|re.I|re.S)

		# loop record in referral table
		combined_urls = []
		for param in refer_table:
			# if table is only a single string value, convert to one element array
			if type(param)!=list and type(param)!=tuple:
				param = [param]

			name = self.page_url_cache_filename
			for n in vals_in_name:
				name = name.replace("$_${" + n + "}", param[int(n)])

			url = self.page_url
			for field in fields_in_url:
				url = url.replace("$_${" + field + "}", param[int(field)])

			combined_urls.append( [url, name, param] )

		return combined_urls
			

	def _validatePage(self, src):
		"""Function to validate all string(s) in page_checking are containing in the page source

		Note:
		Private function for class internal use only
		All string(s) in page_checking are mandatory 

		Args:
		src (str): page html source code 
		"""
		for checkItem in self.page_checking:
			if checkItem not in src:
				print("PAGE CONTENT IS INVALID WHEN VALIDATING PAGE")
				return False
		return True        


	def _parse_result(self, filename, parameter):
		"""Distribute parsing job to parser by "TYPE" field in parser definition

		Note:
		Private function for class internal use only
		Support "RE":Regular Express; "BS":BeautifulSoup

		Args:
		filename (str): local cached html source file 
		parameter (list): values to pass to parser
		"""
		cache_file = open(filename, "r", encoding='UTF-8')
		src = cache_file.read()

		for parser in self.parsers:
			if "TYPE" not in parser:
				continue;

			if parser["TYPE"]=="RE":
				self._parseArrayByRegularExp(src, parser, parameter)
			elif parser["TYPE"]=="BS":
				self._parseArrayByBeautifulSoap(src, parser, parameter)


	def _parseArrayByRegularExp(self, src, parser, parameter):
		"""Parse array by definition in parser using regular expression and update page_state

		Note:
		Private function for class internal use only
		In definition, "NAME" will be the key in page_state; "FILTER" will be the regular expression

		Args:
		parser (dictionary): parser values 
		parameter (list): values to substitute to the regular expression
		"""
		parser_name = parser["NAME"]
		parser_pattern = parser["FILTER"]

		for pindex in range(len(parameter)):
			parser_pattern = parser_pattern.replace("$_${" + str(pindex) + "}", parameter[pindex])

		info = re.findall(parser_pattern, src, re.M|re.I|re.S); 

		if parser_name not in self.page_state:
			self.page_state[parser_name] = info
		else:
			self.page_state[parser_name].extend(info)


	def _parseArrayByBeautifulSoap(self, src, parser, parameter):
		"""Parse array by definition in parser using BeauitfulSoup library and update page_state

		Note:
		Private function for class internal use only
		In definition:
			"NAME" will be the key in page_state; 
			"TAG" will be the target tag e.g. <a>, <div>... 
			"CRITERIA" will be condition to filter the TAG e.g. { "class"="highlight" }
			"FILTER" will be a further filter to the list of elements parsed by the BeautifulSoup

		Args:
		parser (dictionary): parser values 
		parameter (list): values to subsitute to the regular expression
		"""
		parser_name = parser["NAME"]
		parser_tag = parser["TAG"]

		parser_pattern = ""
		if "FILTER" in parser:
			parser_pattern = parser["FILTER"]

		parser_tag_criteria = { }
		if "CRITERIA" in parser:
			parser_tag_criteria = parser["CRITERIA"]

		for pindex in range(len(parameter)):
			parser_pattern = parser_pattern.replace("$_${" + str(pindex) + "}", parameter[pindex])

		soup = BeautifulSoup(src, 'html.parser')
		target = soup.find_all(parser_tag, parser_tag_criteria)

		list = []
		if parser_pattern is not None:
			for line in target:
				filterInfo = re.findall(parser_pattern, line.prettify(), re.M|re.I|re.S)
				if len(filterInfo)>0:
					list.append(filterInfo[0])
		else:
			list = target

		if parser_name not in self.page_state:
			self.page_state[parser_name] = list
		else:
			self.page_state[parser_name].extend(list)

		#print(list)

		
	def _findValueByRegularExp(self, src, pattern):
		"""Parse single value in source code using Regular Expression 

		Note:
		Private function for class internal use only
		Return None if not found

		Args:
		src (str): source code of html
		pattern (str): string of regular expression

		Returns:
		Target string in source
		"""
		info = re.findall(pattern, src , re.M|re.I|re.S); 
		if len(info)>0:
			return info[0]
		return None


	def _findValueByBeautifulSoup(self, src, target, criteria, return_attribute):
		"""Parse single value in source code using BeautifulSoup

		Note:
		Private function for class internal use only
		Return None if not found

		Args:
		src (str): source code of html
		target (str): target tag e.g. <a>, <div>... 
		criteria (dictionary): condition to filter the TAG e.g. { "class"="highlight" }
		return_attribute: attribute of the element which is found by BeautifulSoup

		Returns:
		Target string in source
		"""
		# target, criteria, return_tag
		soup = BeautifulSoup(src, 'html.parser')
		result = soup.find(target, attrs=criteria)
		if result is not None:
			if type(result)==list:
				if return_attribute in str(result[0]):
					return result[0][return_attribute]
			else:
				if return_attribute in str(result):
					return result[return_attribute]
		return None

	
	def _handle_pager(self, web, url, file, parameter):       
		"""Seek all pages of URL and add tasks for parsing each page to queue

		Notes:
		Private function for class internal use only

		Args:
		web (webdriver): selenium browser instance
		url (str): URL of the webpage 
		file (string): naming of the page for file saving 
		parameter (list): value to substitute to filter regular expression in parsing task
		"""
		page_counter = 1

		# if with pager, parse for next page and load next page
		if "TYPE" in self.pager_parser and "TAG" in self.pager_parser and "CRITERIA" in self.pager_parser:
			type = self.pager_parser["TYPE"]

			if type=="RE":
				# to be implemented
				# ...
				pass
			else:
				tag = self.pager_parser["TAG"]
				criteria = self.pager_parser["CRITERIA"]

				srcFilename, src = self._getHtml(web, url, file)

				findingValue = self._findValueByBeautifulSoup(src, tag, criteria, "href")
				while findingValue is not None:
					page_counter = page_counter + 1
					if self.config["site"] not in findingValue:
						url =  self.config["site"] + findingValue

					paging_filename = file + "_" + str(page_counter)
					srcFilename, src = self._getHtml(web, url, paging_filename)
					self._enqueue_task(url, paging_filename, parameter)

					findingValue = self._findValueByBeautifulSoup(src, tag, criteria, "href")


	def add_pages_to_queue(self, web):
		"""Add main page task to a task queue and call _handle_pager() to add sub-pages to queue if needed

		Args:
		web (webdriver): selenium browser instance

		Returns:
		No of urls
		"""
		# get list of merged url 
		actual_urls = self._merge_url()
		for urlInfo in actual_urls:
			self._enqueue_task(urlInfo[0], urlInfo[1], urlInfo[2])
			self._handle_pager(web, urlInfo[0], urlInfo[1], urlInfo[2])

		return len(actual_urls)


	def _enqueue_task(self, url, name, parameter):
		"""Generate a unique task reference and put parameters to a list as the task queue

		Args:
		url (str): URL of the webpage 
		name (string): naming of the page for file saving 
		parameter (list): value to substitute to filter regular expression in parsing task
		"""
		# generate key for the task and add to the queue
		task_key = uuid.uuid4().hex
		self.wait_parsing_list.append([task_key, url, name, parameter])
		# TODO: change wait_parsing_list to a dictionary and use task_key as the key
		# add task_key to a message queue and allow workers to pop, then get and remove record in dictionary and finally acheive the task
		# 


	def dequeue_parse_task(self):
		"""Get a task from the task queue

		Note:
		Return None if queue is empty

		Returns:
		Information of the task include URL, NAME and PARAMETER. Details of return value can be found in _enqueue_task()
		"""
		if self.get_queue_total_task()==0:
			return None

		# should pop top record, get html and parse
		return self.wait_parsing_list.pop(0)


	def get_queue_total_task(self):
		"""Get a total number of tasks in task queue

		Returns:
		Count of element in task queue
		"""
		return len(self.wait_parsing_list)

	
	def bypass_task_in_queue(self, except_task):
		"""Remove leading count of elements in the task queue

		Args:
		except_task (int): Count of tasks to be removed 

		Returns:
		return excepted task count

		Notes:
		Only run when except_task > 0
		"""
		if except_task > 0:
			del self.wait_parsing_list[0:except_task]
			return except_task
		else:
			return 0


	def handle_page_task(self, web, url, file, parameter):
		"""Proceed getting html source code and parsing data. 

		Args:
		web (webdriver): selenium browser instance
		url (str): URL of the webpage 
		file (string): naming of the page for file saving 
		parameter (list): value to substitute to filter regular expression in parsing task

		Returns:
		return save cache file name
		"""
		# try to get file 
		srcFilename, src = self._getHtml(web, url, file)
		# print(srcFilename)

		# parse infomation
		self._parse_result(srcFilename, parameter)

		return srcFilename


	def load_site_data(self, data):
		"""Put previous page extraction data to this page  

		Args:
		data (dictionary): previous page extraction data
		"""
		self.page_state = data


	def _getHtml(self, web, url, file, overwrite=False):
		"""get html source of "url".  

		Note:
		Private function for class internal use only
		If found file in local cache, return from file. Otherwise access url and get the html. Will save html in file

		Args:
		web (webdriver): selenium browser instance
		url (str): URL of the webpage 
		file (string): naming of the page for file saving 
		overwrite (Bool): if True, will get html by access the url no matter cache file exists
		"""
		if file is None:
			return

		url = html.unescape(url)
		with open("extraction.log", "a") as logfile:
			logfile.write(url + "\n")

		dir = os.path.join(self.config["cache_root_dir"], self.page_name)
		if not os.path.exists(dir):
			os.makedirs(dir);

		# check if cache file found, get file cache instead 
		filename = os.path.join(dir, file + ".html");         
		if os.path.exists(filename) and not overwrite: 
			# get by cache
			cache_file = open(filename, "r", encoding='UTF-8')
			src = cache_file.read()
		else:
			# get source
			web.get(url)
			src = web.page_source

		# validation
		if not self._validatePage(src):
			page_retrying = 0
			if url in self.page_retry:
				page_retrying = self.page_retry[url]

			page_retrying = page_retrying + 1
			if page_retrying < self.config["retry"]:
				# delay some second
				self._randomWait(url)
				self.page_retry[url] = page_retrying

				return self._getHtml(web, url, file, True)
			else:
				with open("extraction.log", "a") as logfile:
					logfile.write("Error: " + filename + " [Validation Failure]\n")

		# save as cache
		with open(filename, "w", encoding='UTF-8') as outfile:
			outfile.write(src);

		return filename, src


	def _randomWait(self, url):
		"""Private function to delay running by random time

		Note:
		Private function for class internal use only
		Max random second set in the site configuration

		Args:
		url (str): URL of the webpage 
		"""
		second_wait = random.randint(0, self.config["max_wait"]);
		print("Randomly wait", second_wait, "s and retrying to get page: " + url);
		time.sleep(second_wait);


	def get_data_file_list(self):
		"""Get all data cache file name
		"""
		return [ parser["NAME"] for parser in self.parsers ]


	




class SiteExtractor:
	"""SiteExtractor is class to handle site extracting project. It stores site settings and contains ExtractorPage(s)

	Attributes:
		config (dictionary): Site settings
		site_page_list (dictionary): List of ExtractorPage
		site_state (dictionary): Memory storage to store all data captured by ExtractorPage
		web (webdriver): selenium browser instance
		running_task (int): Completed task index in task queue
	"""

	config = None
	site_page_list = {}
	site_state = {}
	web = None
	running_task = None

	def __init__(self, settings):
		"""Constructor of SiteExtractor

		Note:
		Store the site configs and setup selenium browser instance

		Args:
		settings (dictionary): site setting definition 
		cookie_bypass (bool): flag to indicate complete cookie agreement or not
		"""
		self.config = settings;
		self.cookie_bypass = False

		# global web driver
		option = webdriver.ChromeOptions()     
		option.add_argument("--window-size=1024,1024")	
		option.add_argument("--disable-infobars");	
		option.add_argument("--disable-extensions");
		option.add_argument("--disable-gpu");
		option.add_argument("--disable-dev-shm-usage");
		option.add_argument("--no-sandbox");			
		option.add_argument('--headless')
		option.add_argument("--disable-setuid-sandbox")
		self.web = webdriver.Chrome(options=option);	
		self.web.get(self.config["site"])

		
	def registerPage(self, definition):         
		"""Add ExtractorPage 

		Args:
		definition (dictionary): ExtractorPage definition
		"""
		self.site_page_list[definition["NAME"]] = ExtractorPage(definition, self.config)


	def proceedLogin(self):
		"""Login to the site and get the page access right 
		"""
		pass


	def proceedCookie(self, quitButtonXpath):
		"""Accept site cookie agreement 

		Args:
		quitButtonXpath (str): xpath of accept cookie button
		"""
		cookieQuitButton = WebDriverWait(self.web, 20).until(EC.visibility_of_element_located((By.XPATH, quitButtonXpath)))
		cookieQuitButton.click()
		self.cookie_bypass = True


	def extractPages(self):
		"""Extract all pages defined in registerPage()
		"""
		with open("extraction.log", "w") as logfile:
			logfile.write("Extraction task start at " + str(datetime.datetime.now())  + "\n")
			logfile.write("---------------------------------------------------------------------------------------\n")

		try:      
			aws = None
			step = 0
			total_step = len(self.site_page_list.items())

			# resume task_counter from exception.json if any
			resume_task = 0
			filename = self.config["cache_root_dir"] + "/exception.json";
			if os.path.exists(filename):
				file = open(filename)
				exceptionJson = json.loads(file.read());
				resume_task = exceptionJson["exception_task"]
				file.close();
			
			# loop pages
			for name, pageExtractor in self.site_page_list.items():
				print(f"\nRUNNING EXTRACTION TASK: {name}")
				self.running_task = None

				# check if all artifact file exist, means task has been done                 
				all_data_file_found = True    
				dataFileList = pageExtractor.get_data_file_list()
				if not os.path.exists(self.config["cache_root_dir"] + "/" + name + ".json"): 
					all_data_file_found = False
				else:
					for filename in dataFileList:
						file = self.config["cache_root_dir"] + "/" + filename + ".json"
						if not os.path.exists(file): 
							all_data_file_found = False
							break
				
				# skip if process has been done before, check json file exist
				if not all_data_file_found:
					pageExtractor.load_site_data(self.site_state)

					# enqueue all pages
					pageExtractor.add_pages_to_queue(self.web)

					total_task = pageExtractor.get_queue_total_task()
					# print( "TASK TOTAL: " + str(total_task) )

					if resume_task>0:
						pageExtractor.bypass_task_in_queue(resume_task)

					# while loop till pop return None
					task_counter = resume_task
					with tqdm(total=total_task) as pbar: 
						while True:
							task = pageExtractor.dequeue_parse_task()
							if task is None:
								break;
							# print("Task#" + str(step+1) + ": " + str(task_counter+1) + "/" + str(total_task), task[0], task[1], task[2])

							pageExtractor.handle_page_task(self.web, task[1], task[2], task[3])    # should be handle by multiple external processes

							task_counter = task_counter + 1
							self.running_task = task_counter
							pbar.update(task_counter - pbar.n)


					with open(self.config["cache_root_dir"] + "/" + name + ".json", "w", encoding='UTF-8') as outfile:
						json.dump({"TOTAL_TASK": total_task}, outfile)
				
					for k, v in pageExtractor.get_page_state().items():
						self.site_state[k] = v

						# write data to json
						with open(self.config["cache_root_dir"] + "/" + k + ".json", "w", encoding='UTF-8') as outfile:
							json.dump(v, outfile)

						#if aws is None:
						#	aws = AwsGateway()
						#file_binary = open(self.config["cache_root_dir"] + "/" + k + ".json", "rb").read()
						#aws.upload_file("aicore4wai", "data_collection/", file_binary, k + ".json")
				else:
					# load all data from task
					for filename in dataFileList:
						print("Task already finished. Loading " + name + " from: " + self.config["cache_root_dir"] + "/" + filename + ".json")
						file = open(self.config["cache_root_dir"] + "/" + filename + ".json")
						pageData = json.loads(file.read());
						file.close();
						self.site_state[filename] = pageData

				step = step + 1
		except:
			logging.exception("Encountering error during the scraping!")
			with open("extraction_error.log", "a") as log:
				log.write("--------------------------------------------------------------------------\n")
				traceback.print_exc(file=log)

			if self.running_task is not None:
				with open(self.config["cache_root_dir"] + "/exception.json", "w") as exceptionFile:
					exceptionFile.write('{"exception_task": ' + str(self.running_task) + '}')
		finally:
			self._closeBrowser()

		# zip the cache files by date
		archive_datecode = datetime.datetime.now().strftime("%Y%m%d")
		archive_filename = "./archives/" + self.config["cache_root_dir"] + "_" + archive_datecode
		if not os.path.exists(archive_filename + ".zip"): 
			shutil.make_archive(archive_filename, 'zip', self.config["cache_root_dir"])
			if aws is None:
				aws = AwsGateway()
				file_binary = open(archive_filename + ".zip", "rb").read()
				aws.upload_file("aicore4wai", "data_collection", file_binary, self.config["cache_root_dir"] + "_" + archive_datecode + ".zip")
				print("Upload archive file to s3")
		else:
			print("Archive exist and should be uploaded to s3 before. Skip the process")

		self._transform()
		self._load()


	def _closeBrowser(self):
		"""Release browser instance

		Notes:
		Private function for class internal use only
		"""
		self.web.close();
		self.web.quit(); 


	def _getCachedSource(self, cache_filename):
		"""Utility funtion to have open cache file and return text content

		Args:
		Protected funtion

		Returns:
		None if no file found, text coutent if file found

		Notes:
		Private function for class internal use only
		""" 
		fname = self.config["cache_root_dir"] + "/" + cache_filename
		if os.path.exists(fname): 
			# get by cache
			cache_file = open(fname, "r", encoding='UTF-8')
			src = cache_file.read()
			cache_file.close()
			return src
		else:
			return None


	# for transformation
	def _transform(self):
		"""Implemented function to transform local html cache files to data

		Notes:
		Protected funtion for override
		"""
		pass

	# for load
	def _load(self):
		"""Implemented function to load data to data repository/database

		Notes:
		Protected funtion for override
		"""
		pass

