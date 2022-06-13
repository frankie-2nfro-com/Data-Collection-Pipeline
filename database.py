import psycopg2
from sqlalchemy import create_engine
import os

class Database:
	engine = None
	connection = None
	
	def __init__(self):
		host = os.getenv('SCRAPER_DB_HOST')
		database = os.environ.get('SCRAPER_DB_NAME')
		port = os.environ.get('SCRAPER_DB_PORT')
		user = os.environ.get('SCRAPER_DB_USER')
		password = os.environ.get('SCRAPER_DB_PWD')		
	
		self.host = host
		self.user = user
		self.password = password
		self.db = database
		self.port = port

		self.engine = create_engine(f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}")
		self.connection = self.engine.connect()

	def execute(self, sql):
		return self.engine.execute(sql).fetchall()

	def close(self):
		self.connection.close()
		self.engine.dispose()