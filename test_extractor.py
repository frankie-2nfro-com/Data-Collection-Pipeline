from unittest import TestCase, TestSuite, TextTestRunner
from extractor import SiteExtractor, ExtractorPage

class SiteExtractorTestCases(TestCase):
    def setUp(self):
        self.siteExtractor = SiteExtractor(
        {
            "site":"https://coinmarketcap.com/", 
            "retry":30, 
            "max_wait":5, 
            "cache_root_dir":"./COIN_CACHE"
        })

        definition = {
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

        self.siteExtractor.registerPage(definition)
        self.extractorPage = self.siteExtractor.site_page_list["COIN_LIST_PAGE"]


    def test_registerPage(self):
        definition = {
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

        self.siteExtractor.registerPage(definition)
        self.assertEqual(type(self.extractorPage), ExtractorPage)    
        self.assertEqual(type(self.extractorPage.config), dict)    
        self.assertEqual(self.extractorPage.page_name, definition["NAME"])    
        self.assertEqual(self.extractorPage.page_url, definition["URL"])    
        self.assertEqual(self.extractorPage.page_checking, definition["CHECK"])    
        self.assertEqual(type(self.extractorPage.parsers), list)    


    def test_proceedCookie(self):
        self.siteExtractor.proceedCookie('//*[@id="cmc-cookie-policy-banner"]/div[2]')
        self.assertEqual(self.siteExtractor.cookie_bypass, True)    

    def test_extractPages(self):
        definition = {
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

        self.siteExtractor.registerPage(definition)
        self.siteExtractor.extractPages()
        self.assertEqual(type(self.siteExtractor.site_state["COIN_LIST"]), list)  
        
    def test_get_page_state(self):
        self.assertEqual(type(self.extractorPage.get_page_state()), dict)

    def test_add_pages_to_queue(self):
        urlCount = self.extractorPage.add_pages_to_queue(self.siteExtractor.web)
        self.assertEqual(type(urlCount), int)
        self.assertGreater(urlCount, 0)

    def test_dequeue_parse_task(self):
        self.extractorPage.add_pages_to_queue(self.siteExtractor.web)
        task = self.extractorPage.dequeue_parse_task()
        self.assertEqual(type(task), list)
    
    def test_get_queue_total_task(self):
        self.extractorPage.add_pages_to_queue(self.siteExtractor.web)
        self.assertGreater(self.extractorPage.get_queue_total_task(), 0)
    
    def test_bypass_task_in_queue(self):
        self.extractorPage.add_pages_to_queue(self.siteExtractor.web)
        self.assertEqual(self.extractorPage.bypass_task_in_queue(1), 1)
    
    def test_handle_page_task(self):
        self.extractorPage.add_pages_to_queue(self.siteExtractor.web)
        task = self.extractorPage.dequeue_parse_task()
        filename = self.extractorPage.handle_page_task(self.siteExtractor.web, task[1], task[2], task[3])
        self.assertEqual(type(filename), str)
    
    def test_load_site_data(self):
        self.extractorPage.load_site_data({"test": "yes"})
        self.assertEqual(self.extractorPage.page_state, {"test": "yes"})
    
    def test_get_data_file_list(self):
        parserList = self.extractorPage.get_data_file_list()
        self.assertEqual(type(parserList), list)
    





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
    suite.addTest(SiteExtractorTestCases('test_get_data_file_list'))
    return suite



if __name__ == '__main__':
      runner = TextTestRunner(failfast=True)
      runner.run(suite())
