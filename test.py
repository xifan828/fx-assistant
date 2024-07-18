from ai.service.web_scrapping import TechnicalAnalysisScrapper

scrapper = TechnicalAnalysisScrapper()
text = scrapper.scrape_root_page()
print(text, "\n")
print(scrapper.parse_root_page(text))
