from extractor import SiteExtractor
from transformer import SiteTransformer
import re

def definePages(extractor):
    """Function to define all pages to be extract

    Args:
    extractor (SiteExtractor): SiteExtractor object
    """

    extractor.registerPage(
        {
            "NAME": "COIN_LIST_PAGE", 
            "URL": "https://coinmarketcap.com/",
            "CHECK": ["Today's Cryptocurrency Prices"],
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

    """
            "PAGER_PARSER": {
                "TYPE": "BS",
                "TAG": "a",
                "CRITERIA": { "class":"chevron", "aria-label":"Next page" }
            },
    """

    extractor.registerPage(
        {
            "NAME": "COIN_DETAILS_PAGE", 
            "URL_REFER_TABLE": "COIN_LIST",
            "URL": "https://coinmarketcap.com/currencies/$_${0}/",
            "CHECK": ["Market Cap", "Volume"],
            "URL_CACHE_FILENAME": "$_${0}",
        }
    )

    """
                "PARSER": [
                {
                    "NAME": "COIN_DETAILS",
                    "TYPE": "BS",
                    "TAG": "a",
                    "CRITERIA": { "class": "cmc-link" } ,
                    "FILTER": r'href="/currencies/([^"]*)"'
                }
            ],
    """




# main block to run the scraper, will skip running if other python program import this file
if __name__ == '__main__':
    # EXTRACT
    siteExtractor = SiteExtractor(
        {
            "name": "crypto",
            "site": "https://coinmarketcap.com/", 
            "retry": 30, 
            "max_wait": 5, 
            "cache_root_dir": "./COIN_CACHE"
        }
    )

    # bypass cookie 
    siteExtractor.proceedCookie("/html/body/div[1]/div/div[3]/div[2]/div[2]")

    # bypass login
    #siteExtractor.proceedLogin()      

    definePages(siteExtractor)

    siteExtractor.extractPages()
    

    # TRANSFORM
    siteTransformer = SiteTransformer(
        {
            "cache_root_dir":"./COIN_CACHE",
            "data_root_dir":"./COIN_DATA",
        }
    )
    siteTransformer.runParser(
        {
            "NAME": "COIN_ICON",
            "DIRECTORY": "COIN_DETAILS_PAGE",
            "FILENAME": '*.html', 
            "TYPE": "RE",
            "FILTER": r'<img\s+src="([^"]+)"\s+height="32"\s+width="32"\s+alt="([^"]+)">',
            "FIELD": ["logo_url", "coin_name"],
            "FETCH": "logo_url",
            "FETCH_FILE": "coin_name"
        }
    )  

    # <img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1.png" height="32" width="32" alt="BTC">


    # LOAD
    # ...