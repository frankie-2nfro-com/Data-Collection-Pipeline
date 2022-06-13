from operator import index
import random
from selenium import webdriver
import re
import os
import json
import html
from bs4 import BeautifulSoup
import random
import time
import logging
import uuid
import datetime
#from os import access
#import numpy as np
import pandas as pd
import fnmatch
import requests


class SiteTransformer:
    """SiteTransformer is class to handle transformation of data extracted by SiteExtractor

    Attributes:

    """

    def __init__(self, config):
        """Constructor of SiteTransformer

        Note:
        Store the transformation configuration

        Args:
        config (dictionary): site setting definition
        """
        self.config = config

    def runParser(self, definition):
        """Function to parse data from cached html files and data json

        Args:
        definition (dictionary): transformation definition 
        """
        name = definition["NAME"]
        dir = definition["DIRECTORY"]
        fname = definition["FILENAME"]
        filter = definition["FILTER"]

        fields = definition["FIELD"]

        fetch = None
        if "FETCH" in definition:
            fetch = definition["FETCH"]

        fetch_file = None
        if "FETCH_FILE" in definition:
            fetch_file = definition["FETCH_FILE"]


        filename = self.config["data_root_dir"] + "/" + name + ".json";
        if os.path.exists(filename):
            print("Transformation: " + name + " has been done already")
            return

        transformer_log = {}

        result = []
        for file in os.listdir(self.config["cache_root_dir"] + "/" + dir):
            if fnmatch.fnmatch(file, fname):
                filename = os.path.join(self.config["cache_root_dir"] + "/" + dir, file);         
                src_file = open(filename, "r", encoding='UTF-8')
                src = src_file.read()
                src_file.close()

                fields_in_src = re.findall(filter, src, re.M|re.I|re.S)
                for line in fields_in_src:
                    result.append(line)

        # save file to 
        if not os.path.exists(self.config["data_root_dir"]):
            os.makedirs(self.config["data_root_dir"]);

        df = pd.DataFrame(result, columns=fields)
        df.to_csv(self.config["data_root_dir"] + "/" + name + ".csv", index=False)

        transformer_log["data_count"] = len(result)

        # fetch
        if fetch is not None:
            fetch_url = definition["FETCH"]
            fetch_file = definition["FETCH_FILE"]

            if not os.path.exists(self.config["data_root_dir"] + "/FETCH"):
                os.makedirs(self.config["data_root_dir"] + "/FETCH");

            fetch_count = 0
            for index, row in df.iterrows():
                url = row[fetch_url]
                fname = row[fetch_file]
                url_parts = url.split(".")

                fetch_filename = self.config["data_root_dir"] + "/FETCH/" + fname + "." + url_parts[-1]
                if not os.path.exists(fetch_filename):
                    response = requests.get(url)
                    file = open(fetch_filename, "wb")
                    file.write(response.content)
                    file.close()
                    fetch_count = fetch_count + 1

            transformer_log["fetch_count"] = fetch_count

        # save log file
        with open(self.config["data_root_dir"] + "/" + name + ".json", "w", encoding='UTF-8') as outfile:
            json.dump(transformer_log, outfile)

                    