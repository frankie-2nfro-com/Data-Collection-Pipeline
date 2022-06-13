from extractor import SiteExtractor
from transformer import SiteTransformer
import re
import pandas as pd
from pandas import json_normalize
import json
from database import Database
import os
from bs4 import BeautifulSoup

def definePages(extractor):
	"""Function to define all pages to be extract

	Args:
	extractor (SiteExtractor): SiteExtractor object
	"""

	extractor.registerPage(
		{
			"NAME": "TRAINER_LIST_PAGE", 
			"URL": "https://racing.hkjc.com/racing/information/Chinese/Trainers/TrainerRanking.aspx",
			"CHECK": ["練馬師", "出馬總數"],
			"PARSER": [
				{
					"NAME": "TRAINER_LIST",
					"TYPE": "BS",
					"TAG": "a",
					"FILTER": r'TrainerId=(.*?)&amp;Season=Current.*?>\s+(.*?)\s+</a>'
				}
			],
		}
	)

	extractor.registerPage(
		{
			"NAME": "TRAINER_HOME_PAGE", 
			"URL_REFER_TABLE": "TRAINER_LIST",
			"URL": "https://racing.hkjc.com/racing/information/Chinese/Trainers/TrainerProfile.aspx?TrainerId=$_${0}&Season=Current", 
			"CHECK": ["出馬總數"],
			"URL_CACHE_FILENAME": "$_${0}",
		}
	)

	extractor.registerPage(
		{
			"NAME": "TRAINER_HORSE_RACE_PAGE", 
			"URL_REFER_TABLE": "TRAINER_LIST",
			"URL": "https://racing.hkjc.com/racing/information/Chinese/Trainers/TrainerPastRec.aspx?TrainerId=$_${0}&Season=Current", 
			"CHECK": ["出馬紀錄"],
			"URL_CACHE_FILENAME": "$_${0}",
			"PARSER": [ 
				{
					"NAME": "RACE_LIST",
					"TYPE": "BS",
					"TAG": "tr",
					"FILTER": r'<a href="/racing/information/Chinese/Racing/LocalResults.aspx(.*?)".*?>\s+([0-9]*)\s+</a>\s+</td>\s+<td class="f_tal f_ffChinese">\s+([\w]+)\s+</td>'
				}
			], 
		}
	)

	"""
			"PAGER_PARSER": {
				"TYPE": "BS",
				"TAG": "a",
				"CRITERIA": { "class":"f_fr" }
			},
	"""

	extractor.registerPage(
		{
			"NAME": "RACE_PAGE", 
			"URL_REFER_TABLE": "RACE_LIST",
			"URL": "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx$_${0}", 
			"CHECK": ["賽事日期", "派彩"],
			"URL_CACHE_FILENAME": "$_${1}",
			"PARSER": [
				{
					"NAME": "HORSE_LIST",
					"TYPE": "BS",
					"TAG": "td",
					"CRITERIA": { "style": "white-space: nowrap;" } ,
					"FILTER": r'.*?Horse.aspx(.*?)">\s+($_${2})\s+</a>'
				}
			],
		}
	)

	"""
	extractor.registerPage(
		{
			"NAME": "HORSE_RACE_PAGE", 
			"URL_REFER_TABLE": "HORSE_LIST",
			"URL": "https://racing.hkjc.com/racing/information/Chinese/Horse/Horse.aspx$_${0}&Option=1", 
			"CHECK": ["往績紀錄"],
			"URL_CACHE_FILENAME": "$_${1}",
		}
	)

	extractor.registerPage(
		{
			"NAME": "HORSE_TRAIN_PAGE", 
			"URL_REFER_TABLE": "HORSE_LIST",
			"URL": "https://racing.hkjc.com/racing/information/Chinese/Trackwork/TrackworkResult.aspx$_${0}", 
			"CHECK": ["往績紀錄"],
			"URL_CACHE_FILENAME": "$_${1}",
		}
	)
	"""


class HKJCExtractor(SiteExtractor):
	def _transform(self):
		print("transform now....")

		# get trainer table
		trainer_table_df = self.__transformTrainerTable()        # return pandas table

		all_trainer_race_list = {}

		# clean up trainer_race_horse table
		df = pd.DataFrame ([], 
			columns = [
				'trainer_code', 
				'race_code', 
				'horse_name', 
				'race_date', 
				'venue',
				'race_no',
				'venue_track_type',
				'track_name',
				'going',
				'draw',
				'marks',
				'jockey',
				'weight',
				'load',
				'gear',
				'odds',
				'total_horse',
				'result'
			]
		).set_index(['trainer_code', 'race_code', 'horse_name'])
		db = Database()
		df.to_sql('trainer_statistic', db.engine, if_exists='replace')
		df.to_sql('trainer_race_horse', db.engine, if_exists='replace')
		db.close()

		# loop trainer
		for index, row in trainer_table_df.iterrows():
			# get trainer home page - TRAINER_HOME_PAGE
			trainer_home_page_cache_file = "TRAINER_HOME_PAGE/" + index + ".html"
			dir = os.path.join(self.config["cache_root_dir"], trainer_home_page_cache_file)
			if not os.path.exists(dir): 
				# throw error
				print("Error to open trainer homepage, check extracotor download file normally")
				break;

			# parse trainer information
			trainer_statistic = self.__transformTrainerStatistic(index, trainer_home_page_cache_file)

			# TRAINER_HORSE_RACE_PAGE
			fcount_code = ""
			fcount = 1
			while True:
				trainer_horse_race_page_cache_file = "TRAINER_HORSE_RACE_PAGE/" + index + fcount_code + ".html"
				dir = os.path.join(self.config["cache_root_dir"], trainer_horse_race_page_cache_file)
				if not os.path.exists(dir): break

				# parse race horse info
				self.__transformTrainerHorseRaceRecord(index, trainer_horse_race_page_cache_file)
				
				fcount = fcount + 1
				fcount_code = "_" + str(fcount)


	def __transformTrainerTable(self):
		# needed source file
		src = self._getCachedSource("/TRAINER_LIST_PAGE/TRAINER_LIST_PAGE.html")
		data_src = self._getCachedSource("TRAINER_LIST.json")
		jsdata = json.loads(data_src);
		df = pd.DataFrame (jsdata, columns = ['trainer_code', 'trainer_name']).set_index('trainer_code')

		db = Database()
		df.to_sql('trainer', db.engine, if_exists='replace')
		table = pd.read_sql_table('trainer', db.engine).set_index('trainer_code')
		db.close()

		return table

	def __transformTrainerStatistic(self, code, file):
		html = self._getCachedSource(file)

		soup = BeautifulSoup(html, 'html.parser')
		target = soup.find_all("table", {"class":"table_bd"})
		info_text = target[0].text

		filterInfo1 = re.findall(r'過去10個賽馬日獲勝次數\s+:\s+([\d]+)\n', info_text, re.M|re.I|re.S)
		filterInfo2 = re.findall(r'出馬總數\s+:\s+([\d]+)\n', info_text, re.M|re.I|re.S)
		filterInfo3 = re.findall(r'冠\s+:\s+([\d]+)\n', info_text, re.M|re.I|re.S)
		filterInfo4 = re.findall(r'亞\s+:\s+([\d]+)\n', info_text, re.M|re.I|re.S)
		filterInfo5 = re.findall(r'季\s+:\s+([\d]+)\n', info_text, re.M|re.I|re.S)
		filterInfo6 = re.findall(r'冠\s+:\s+([\d]+)\n', info_text, re.M|re.I|re.S)

		record = {
			"trainer_code": code, 
			"last10_win":filterInfo1[0],
			"race_total":filterInfo2[0],
			"total_w":filterInfo3[0],
			"total_q":filterInfo4[0],
			"total_p":filterInfo5[0],
			"total_f":filterInfo6[0],
		}

		df = pd.DataFrame([record]).set_index("trainer_code")

		# TODO: how to set primary key here
		# ...

		db = Database()
		df.to_sql('trainer_statistic', con=db.engine, if_exists='append', index=True)
		db.close()

		return df

	def __transformTrainerHorseRaceRecord(self, code, file):
		html = self._getCachedSource(file)

		soup = BeautifulSoup(html, 'html.parser')
		table = soup.find("table", {"class":"table_bd"})
		tbody = table.find("tbody")
		trs = tbody.find_all("tr")

		list = []
		for row in trs:
			tds = row.find_all("td")
			if len(tds)==0: continue

			# <td><a href="/racing/information/Chinese/Racing/LocalResults.aspx?RaceDate=2021/11/03&amp;Racecourse=HV&amp;RaceNo=6">146</a></td>
			race_link = tds[0].prettify()
			race_link_info = re.findall(r'RaceDate=(.*?)&.*?Racecourse=(.*?)&.*?RaceNo=(.*?)">\s*(.*?)\s*</a>', race_link, re.M|re.I|re.S)
			horse_name = tds[1].text
			race_result = tds[2].text
			race_date = tds[3].text
			race_track = tds[4].text
			race_length = tds[5].text
			race_going = tds[6].text
			race_draw = tds[7].text
			horse_point = tds[8].text
			horse_odds = tds[9].text
			horse_jockey = tds[10].text
			horse_gear = tds[11].text
			horse_weight = tds[12].text
			horse_load = tds[13].text

			# validation
			if "/" not in race_result: continue

			race_result_parts = race_result.split("/")
			race_total_horse = race_result_parts[1]
			horse_result = race_result_parts[0]

			race_venue_type = ""
			race_track_name = ""
			if "全天候" in race_track:
				race_venue_type = "全天候"
				race_track_name = ""
			else:
				race_venue_type = "草地"
				rtInfo = race_track.split('"')
				race_track_name = rtInfo[1]
		
			list.append([
				code,
				race_link_info[0][3],
				horse_name,
				race_date,
				race_link_info[0][1],
				race_link_info[0][2],
				race_venue_type,
				race_track_name,
				race_going,
				race_draw,
				horse_point, 
				horse_jockey, 
				horse_weight, 
				horse_load, 
				horse_gear,
				horse_odds,
				race_total_horse,
				horse_result,
			])

			self.__transformRaceResult(horse_name, "RACE_PAGE/" + race_link_info[0][3] + ".html")

			self.__transformHorseRaceRecord(horse_name, "HORSE_RACE_PAGE/" + horse_name + ".html", race_date)

			self.__transformHorseTrainRecord(horse_name, "HORSE_TRAIN_PAGE/" + horse_name + ".html", race_date)

		
		df = pd.DataFrame (list, 
			columns = [
				'trainer_code', 
				'race_code', 
				'horse_name', 
				'race_date', 
				'venue',
				'race_no',
				'venue_track_type',
				'track_name',
				'going',
				'draw',
				'marks',
				'jockey',
				'weight',
				'load',
				'gear',
				'odds',
				'total_horse',
				'result'
			]
		).set_index(['trainer_code', 'race_code', 'horse_name'])

		# TODO: how to set primary key here
		# ...

		# put record to database
		db = Database()
		df.to_sql('trainer_race_horse', db.engine, if_exists='append')
		db.close()

	def __transformRaceResult(self, horse, file):
		# get race info - RACE_PAGE
		#html = self._getCachedSource(file)
		#print(html)

		# ...
		pass

	def __transformHorseRaceRecord(self, horse, file, race_date):
		# get horse home page - HORSE_RACE_PAGE
		#html = self._getCachedSource(file)
		#print(html)

		# ...
		pass

	def __transformHorseTrainRecord(self, horse, file, race_date):
		# get horse train page - HORSE_TRAIN_PAGE
		#html = self._getCachedSource(file)
		#print(html)

		# ...
		pass
	
  

# main block to run the scraper, will skip running if other python program import this file
if __name__ == '__main__':
	# EXTRACT
	siteExtractor = HKJCExtractor(
		{
			"name": "hkjc",
			"site": "https://racing.hkjc.com", 
			"retry": 30, 
			"max_wait": 5, 
			"cache_root_dir": "./CACHE"
		}
	)

	definePages(siteExtractor)

	# bypass cookie 
	#siteExtractor.proceedCookie("")

	# bypass login
	#siteExtractor.proceedLogin()      

	siteExtractor.extractPages()