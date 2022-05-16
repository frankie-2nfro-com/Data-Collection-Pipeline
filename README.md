# Data-Collection-Pipeline
This repository is for my AiCore project for data collection. 

And this README is for the description of this project and answering the questions of the project milestones. 

## Milestone 1 - Decide the website you are going to collect data from
I am working with horse racing data for several years and still interesting in digging more 'useful knowledge' on this area. So I will try to collect data from a horse racing web site. I will try to learn again from AiCore and compare the method between mine and AiCore. And hope it will have some inspiration to improve my skill.

## Milestone 2 - Prototype finding the individual page for each entry

Many website using front-end rendering and cookie to limit accessing html directly from the http protocol althrogh it will be the most efficient way to capture the data. And now I will use selenium to get the source and content of the website. But it needs to sort out some way to increase the speed of capturing data later. 

### Parser
I will use BeautifulSoap and Regular Expression to parse inforamtion from the website. 

### Extract, Transform and Load (ETL)
I will divide the whole process into three parts namely Extract, Transform and Load. 

#### Extract
Get all html source files in the local repository 

#### Transform
Parse local source files and get needed information to local database or files

#### Load
Load local dataset to the central database with all history data 

## Milestone 3 - Retrieve data from details page

To make the program to be highly reusable for different website scraping, I will try to using rule definition to define the scraping behaviours. As mention above in Milestone 2, I will extract webpages first. And then will parse all information needed in the "Transform" step. And "Load" all information to the data repository. 

Here is an example how I define extraction behavour for a website:

```
extractor.registerPage(
        {
            "NAME": "COIN_LIST_PAGE", 
            "URL": "https://coinmarketcap.com/",
            "CHECK": ["Today's Cryptocurrency Prices"],
            "PAGER_PARSER": {
                "TYPE": "BS",
                "TAG": "a",
                "CRITERIA": { "class":"chevron", "aria-label":"Next page" }
            },
            "PARSER": [
                {
                    "NAME": "COIN_LIST",
                    "TYPE": "BS",
                    "TAG": "a",
                    "CRITERIA": { "class": "cmc-link" } ,
                    "FILTER": r'href="/currencies/([^"/]*)/"'
                }
            ],
        }
    )
```

In above code, it will 1) get source of "URL"; 2) Parse all cryptocurrency detail page links; 3) Load all "next page" and get the source like 1) and 2). It will then create folder to store the parsed data into local json file for further steps. 

The implementation purpose is that the logic in each site would not be embedded to the main scraper class and can be reused for future data collection.


