import requests
from datetime import datetime, date
from bs4 import BeautifulSoup
from ai.config import Config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

class FED:
    dates_fed = [date(2024, 6, 12), date(2024, 7, 31), date(2024, 9, 18), date(2024, 11, 7), date(2024, 12, 18)]

    def __init__(self):
        pass

    def check_dates(self):
        today = date.today()
        previous_fed_dates = [i for i in self.dates_fed if i <= today]
        latest_fed_date = previous_fed_dates[-1]
        return latest_fed_date
    
    def check_file_exist(self, date):
        files = []
        formated_date = date.strftime('%Y%m%d')
        for file_name in os.listdir("data/central_banks"):
            if (file_name == f"fed_{formated_date}_statement.txt") or (file_name == f"fed_{formated_date}_minutes.txt"):
                files.append(file_name)
        return files
    
    def summarize(self, statement, minutes):
        model = Config(model_name="gpt-4o-mini", temperature=0.2, max_tokens=512).get_model()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "As an expert forex analyst specializing in EUR/USD pair technical analysis. You will be provided with latest announcements from the Federal Open Market Committee US. You task is to summarize it. Start your output with ## Federal Open Market Committee US"),
            ("user", "Below is the statement:\n{statement}\nBelow is the Minutes:\n{minutes}")
        ])
        chain = prompt | model | StrOutputParser()
        summary = chain.invoke({"minutes": minutes, "statement": statement})
        return summary
    
    def scrape_statement(self, date):
        formated_date = date.strftime('%Y%m%d')
        url = f"https://www.federalreserve.gov/newsevents/pressreleases/monetary{formated_date}a.htm"
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            div_content = soup.find('div', class_="col-xs-12 col-sm-8 col-md-8")
            clean_text = div_content.get_text(strip=True, separator='\n')
            file_name = f"data/central_banks/fed_{formated_date}_statement.txt"
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(clean_text)
            return clean_text
        else:
            print(f"Failed to scrape FED statement on {formated_date}. url: {url}")
            content = ""
            return content
    
    def scrape_minutes(seld, date):
        formated_date = date.strftime('%Y%m%d')
        url = f"https://www.federalreserve.gov/monetarypolicy/fomcminutes{formated_date}.htm"
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            div_content = soup.find('div', class_="col-xs-12 col-sm-8 col-md-9")
            clean_text = div_content.get_text(strip=True, separator='\n')
            model = Config(model_name="gpt-4o-mini", temperature=0.2).get_model()
            prompt = ChatPromptTemplate.from_messages([
                ("system", "As an expert forex analyst specializing in EUR/USD pair technical analysis. You will be provided with the Minutes of the Federal Open Market Committee. You task is to summarize it."),
                ("user", "{minutes}")
            ])
            chain = prompt | model | StrOutputParser()
            summary = chain.invoke({"minutes": clean_text})
            file_name = f"data/central_banks/fed_{formated_date}_minutes.txt"
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(summary)
            return summary
        else:
            print(f"Failed to scrape FED minutes on {formated_date}. url: {url}")
            content = ""
            return content

    def run(self):
        latest_fed_date = self.check_dates()
        existed_files = self.check_file_exist(latest_fed_date)
        print(existed_files)
        if len(existed_files) == 0:
            fed_statement = self.scrape_statement(latest_fed_date)
            if fed_statement == "":
                previous_dates = [date for date in self.dates_fed if date < latest_fed_date]
                latest_previous_fed_date = previous_dates[-1]
                existed_files = self.check_file_exist(latest_previous_fed_date)
            else:
                existed_files = self.check_file_exist(latest_fed_date)

        date_str = existed_files[0].split("_")[1]

        if len(existed_files) == 1:
            fed_minutes = self.scrape_minutes(latest_fed_date)
            if fed_minutes == "":
                with open("data/central_banks/"+existed_files[0], "r", encoding='utf-8') as file:
                    fed_statement = file.read()
                summary_file_name = f"data/central_banks/fed_{date_str}_summary_single.txt"
                if os.path.exists(summary_file_name):
                    with open(summary_file_name, "r", encoding='utf-8') as file:
                        summary = file.read()
                else:
                    summary = self.summarize(fed_statement, fed_minutes)
                    with open(summary_file_name, "w", encoding='utf-8') as file:
                        file.write(summary)
            else:
                existed_files = self.check_file_exist(latest_fed_date)

        if len(existed_files) == 2:
            for file_name in existed_files:
                if "statement" in file_name: 
                    with open("data/central_banks/"+file_name, "r", encoding='utf-8') as file:
                        fed_statement = file.read()
                if "minutes" in file_name:
                    with open("data/central_banks/"+file_name, "r", encoding='utf-8') as file:
                        fed_minutes = file.read()
            summary_file_name = f"data/central_banks/fed_{date_str}_summary_complete.txt"
            if os.path.exists(summary_file_name):
                    with open(summary_file_name, "r", encoding='utf-8') as file:
                        summary = file.read()
            else:
                summary = self.summarize(fed_statement, fed_minutes)
                with open(summary_file_name, "w", encoding='utf-8') as file:
                    file.write(summary)
        return summary

class ECB:
    root_page_url = "https://www.ecb.europa.eu/press/press_conference/html/index.en.html"
    main_page_url = "https://www.ecb.europa.eu"

    def __init__(self):
        pass

    def scrape_website(self, website):
        	
        response = requests.get(website)
        if response.status_code == 200:
            return response.text
        else:
            return None
        
    def save_to_txt(self, text, file_name):
        with open(file_name, "w", encoding="utf-8") as file:
                file.write(text)
    
    def read_from_txt(self, file_name):
        with open(file_name, "r", encoding='utf-8') as file:
            text = file.read()
        return text

    def find_date(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        button = soup.find('button', class_='date-picker icon -csv-file-2')
        if button:
            date_str = button.text.strip()
            date_obj = datetime.strptime(date_str, '%d %B %Y')
            formatted_date = date_obj.strftime('%Y%m%d')
            return formatted_date
        return None

    def find_press_release_href(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        divs = soup.find_all('div', class_='content-box')
        for div in divs:
            if div.find('a', string='Press release'):
                return div.find('a', string='Press release')['href']
        return None

    def find_monetary_policy_statement_href(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        divs = soup.find_all('div', class_='content-box')
        for div in divs:
            if div.find('a', string='Monetary policy statement'):
                return div.find('a', string='Monetary policy statement')['href']
        return None
    
    def get_press_release(self, press_realease_html_content):
        soup = BeautifulSoup(press_realease_html_content, 'html.parser')
        main_content = soup.find('main')
        markdown = []

        # Extract the publication date
        publication_date = soup.find('p', class_='ecb-publicationDate')

        # Extract and format the rest of the content
        for element in main_content.find_all(['p', 'h2', 'h1']):
            if element.name == 'h1':
                markdown.append(f"## {element.text.strip()}\n")
                if publication_date:
                    markdown.append(f"**Publication Date:** {publication_date.text.strip()}\n")

            if element.name == 'h2':
                markdown.append(f"### {element.text.strip()}\n")
            elif element.name == 'p' and 'ecb-publicationDate' not in element.get('class', []):
                markdown.append(f"{element.text.strip()}\n")
        #return section
        text = ''.join(markdown)

        return text
    
    def get_monetary_policy_statement(self, monetary_policy_statement_html_content):
        soup = BeautifulSoup(monetary_policy_statement_html_content, 'html.parser')
        main_content = soup.find('main')
        markdown = []

        # Extract the publication date
        publication_date = soup.find('p', class_='ecb-publicationDate')

        # Extract and format the rest of the content
        for element in main_content.find_all(['p', 'h2', 'h1']):
            if element.name == 'h1':
                markdown.append(f"## {element.text.strip()}\n")
                if publication_date:
                    markdown.append(f"**Publication Date:** {publication_date.text.strip()}\n")

            if element.name == 'h2':
                markdown.append(f"### {element.text.strip()}\n")
            elif element.name == 'p' and 'ecb-publicationDate' not in element.get('class', []) and element.find("strong"): 
                markdown.append(f"Question: {element.text.strip()}\n")
            elif element.name == 'p' and 'ecb-publicationDate' not in element.get('class', []): 
                markdown.append(f"{element.text.strip()}\n")
        #return section
        return ''.join(markdown)

    def summarize_monetary_policy_statement(self, monetary_policy_statement):
        model = Config(temperature=0.2).get_model()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "As an expert forex analyst specializing in EUR/USD pair technical analysis. You will be provided with the MONETARY POLICY STATEMENT PRESS CONFERENCE together with questions and answers from ECB officials. You task is to summarize it."),
            ("user", "{content}")
        ])
        chain = prompt | model | StrOutputParser()
        summary = chain.invoke({"content": monetary_policy_statement})
        return summary
    
    def summarize(self, press_release, monetary_policy):
        model = Config(model_name="gpt-4o-mini", temperature=0.2, max_tokens=512).get_model()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "As an expert forex analyst specializing in EUR/USD pair technical analysis. You will be provided with latest announcements from the European Central Bank. You task is to summarize it. Start your output with ## European Central Bank"),
            ("user", "Below is the Monetary policy decisions:\n{press_release}\nBelow is the monetary policy statement with Q&A:\n{monetary_policy}")
        ])
        chain = prompt | model | StrOutputParser()
        summary = chain.invoke({"press_release": press_release, "monetary_policy": monetary_policy})
        return summary
    
    def check_file_exist(self, date):
        files = []
        for file_name in os.listdir("data/central_banks"):
            if (file_name == f"ecb_{date}_statement.txt") or (file_name == f"ecb_{date}_qa.txt"):
                files.append(file_name)
        return files
    
    def run(self):
        html_content = self.scrape_website(self.root_page_url)
        date = self.find_date(html_content)
        existed_files = self.check_file_exist(date)
        print(existed_files)
        if len(existed_files) == 0:
            press_release_url = self.main_page_url + self.find_press_release_href(html_content)
            press_release_html_content = self.scrape_website(press_release_url)
            presse_release = self.get_press_release(press_release_html_content)
            try:
                monetary_policy_url = self.main_page_url + self.find_monetary_policy_statement_href(html_content)
                monetary_policy_html_content = self.scrape_website(monetary_policy_url)
                monetary_policy = self.get_monetary_policy_statement(monetary_policy_html_content)
                monetary_policy_summary = self.summarize_monetary_policy_statement(monetary_policy)
            except:
                monetary_policy_summary = ""
            self.save_to_txt(presse_release, f"data/central_banks/ecb_{date}_statement.txt")
            if monetary_policy_summary != "":
                self.save_to_txt(monetary_policy_summary, f"data/central_banks/ecb_{date}_qa.txt")
                summary = self.summarize(press_release=presse_release, monetary_policy=monetary_policy_summary)
                self.save_to_txt(summary, f"data/central_banks/ecb_{date}_summary_complete.txt")
            else:
                summary = self.summarize(press_release=presse_release, monetary_policy=monetary_policy_summary)
                self.save_to_txt(summary, f"data/central_banks/ecb_{date}_summary_single.txt")
            return summary
        
        if len(existed_files) == 1:
            presse_release = self.read_from_txt(f"data/central_banks/ecb_{date}_statement.txt")
            try:
                monetary_policy_url = self.main_page_url + self.find_monetary_policy_statement_href(html_content)
                monetary_policy_html_content = self.scrape_website(monetary_policy_url)
                monetary_policy = self.get_monetary_policy_statement(monetary_policy_html_content)
                monetary_policy_summary = self.summarize_monetary_policy_statement(monetary_policy)
            except:
                monetary_policy_summary = ""
            if monetary_policy_summary != "":
                self.save_to_txt(monetary_policy_summary, f"data/central_banks/ecb_{date}_qa.txt")
                summary = self.summarize(press_release=presse_release, monetary_policy=monetary_policy_summary)
                self.save_to_txt(summary, f"data/central_banks/ecb_{date}_summary_complete.txt")
            else:
                summary_file_path = f"data/central_banks/ecb_{date}_summary_single.txt"
                if os.path.exists(summary_file_path):
                    summary = self.read_from_txt(summary_file_path)
                else:
                    summary = self.summarize(press_release=presse_release, monetary_policy=monetary_policy_summary)
                    self.save_to_txt(summary, summary_file_path)
            return summary

        if len(existed_files) == 2:
            presse_release = self.read_from_txt(f"data/central_banks/ecb_{date}_statement.txt")
            monetary_policy_summary = self.read_from_txt(f"data/central_banks/ecb_{date}_qa.txt")
            summary_file_path = f"data/central_banks/ecb_{date}_summary_complete.txt"
            if os.path.exists(summary_file_path):
                summary = self.read_from_txt(summary_file_path)
            else:
                summary = self.summarize(press_release=presse_release, monetary_policy=monetary_policy_summary)
                self.save_to_txt(summary, summary_file_path)
            return summary

    
if __name__ == "__main__":
    fed = FED()
    print(fed.run())

    ecb = ECB()
    print(ecb.run())