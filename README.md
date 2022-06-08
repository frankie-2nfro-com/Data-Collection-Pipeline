# Data-Collection-Pipeline
This repository is for my AiCore project for data collection. 

And this README is for the description of this project and answering the questions of the project milestones. 

## Milestone 1 - Decide the website you are going to collect data from
I am working with horse racing data for several years and still interesting in digging more 'useful knowledge' on this area. So I will try to collect data from a horse racing web site. I will try to learn again from AiCore and compare the method between mine and AiCore. And hope it will have some inspiration to improve my skill.

## Milestone 2 - Prototype finding the individual page for each entry

Many website using front-end rendering and cookie to limit accessing html directly from the http protocol althrogh it will be the most efficient way to capture the data. And now I will use selenium to get the source and content of the website. But it needs to sort out some way to increase the speed of capturing data later. 

### Parser
I will use BeautifulSoap and Regular Expression to parse inforamtion from the website. 

### Process
I will divide the whole process into two steps. Firstly I will extract all page source file from my target website to local storage. After making sure all need webpages are downloaded, I will start the transform process to get needed information from the cached htmls.

## Milestone 3 - Retrieve data from details page

To make the program to be highly reusable for different website scraping, I will try to using rule definition to define the extraction behaviours. As mention above in Milestone 2, I will extract webpages first. And then will parse all information needed in the "Transform" step. 

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

To prove my method, I tried to define two set of scraper to capture two websites. One has six target webpages with hierarchy. After the main page, I will collect 36 subpages. In those subpages, it will have another detail pages for each and it will have multiple pages because of the pager. It totally collect  185 pages. Finally, In those pages, I will get needed links and then collect all pages. It is 7903 pages each for the rest of the pages. 

And anoher website, I captured all links in main page. It is with pager and total have 10112 links. And then I capture all 10112 details and save images in the local directory. 

And definition parser work well for my situation.

## Milestone 4 - Documentation and testing

All public method in the class will be unit tested in test cases. It will make sure all the functions produce expected result when passing in needed arguments. The unit test tool will be used is python build in unittest library. To better control the order of testing functions, it will arrange the order of execution by a TestSuite as follows

```
def suite():
    suite = TestSuite()
    suite.addTest(SiteExtractorTestCases('test_registerPage'))
    suite.addTest(SiteExtractorTestCases('test_proceedCookie'))
    suite.addTest(SiteExtractorTestCases('test_extractPages'))
    suite.addTest(SiteExtractorTestCases('test_get_page_state'))
    suite.addTest(SiteExtractorTestCases('test_add_pages_to_queue'))
    suite.addTest(SiteExtractorTestCases('test_dequeue_parse_task'))
    suite.addTest(SiteExtractorTestCases('test_get_queue_total_task'))
    suite.addTest(SiteExtractorTestCases('test_bypass_task_in_queue'))
    suite.addTest(SiteExtractorTestCases('test_handle_page_task'))
    suite.addTest(SiteExtractorTestCases('test_load_site_data'))
    suite.addTest(SiteExtractorTestCases('test_getDataFileList'))
    return suite
```

To run the unit tests:

```
python -m unittest test_extractor.py -v

..RUNNING EXTRACTION TASK: COIN_LIST_PAGE
Task already finished. Loading COIN_LIST_PAGE from: ./COIN_CACHE/COIN_LIST.json
.........
----------------------------------------------------------------------
Ran 11 tests in 39.464s

OK
```

## Milestone 5 - Scalably store the data
Setting up AWS services is a big challenge for me as I had some bad experience getting large amount charged by amazon. So I setup carefully to make sure no unnecessary function added for this project to use Lambda, storage service and RDS. 

### Services adoped in this project

#### Storage for raw data and image data
The scaper will save json and image file to S3 storage via boto3

#### Relational database for tabular data
The parsed data from scaper with uuid generated unique key will be transfered to the AWS RDS via psycopy2 and sqlalchemy

## Milestone 6 - Containerise scraper
It is quite good to run scraper in Docker for easily replicate the environment. However, I need to consider how to handle the exception and other abnormal running issues. I may need to store the states in database for resuming the process. Another way is decomposite the scraping process in small parts and let different Docker images to handle to simplify the error handling. 

## Milestone 7 - Make the scraping scalable
In this milestone, I try to using Docker and EC2 instance to run my scraper in the Cloud. Using Docker allow me to deploy the changes easily. But I need to automate the whole process so that I can update the Docker image automatically and EC2 will keep running the latest version of my scraper. 

### Scraper Optimization

#### Cache mechanism
When scraping web content, some pages are repeatedly linked. So to avoid duplicated scraping, I will use the key as the filename to make sure the file is nonexist before loading. It will reduce the traffic and resources for the scraper. 

#### Relational Database
Rather than using cache file named, data in relational database are easily to maintain the uniquenesses. The table primary key constrain make sure the record is single stored in the database. I setup a postgres in AWS so that the scraper running in EC2 can save data and states to this remoted database. 

#### Exception
Even unit test is passed in the previous milestone, it is still hard to ensure the running can finished normally as it is rely on a third party website. So it is important to have a way to resume the scraping process from break point instead of running from the beginning everytime. The progress state will be store to a local file. So the program will load it and run at the last break point. 




