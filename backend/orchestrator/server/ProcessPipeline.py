import json
import os
from backend.utils.parameters import CURRENCY_PAIRS
from typing import List, Dict, Union

class ProcessPipeline:
    def __init__(self):
        self.process_dir_path = os.path.join("data", "process")
        if not os.path.exists(self.process_dir_path):
            os.makedirs(self.process_dir_path)

        self.scrape_dir_path = os.path.join("data", "scrape")

        self.scrape_results = self._load_scrape_results()

        self.scrape_results_prev = self.scrape_results[-2]["data"] if len(self.scrape_results) > 1 else None

        self.scrape_results_curr = self.scrape_results[-1]["data"] 
    
    def _load_json(self, file_path: str) -> List[Dict]:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    
    def _save_json(self, data: List[Dict], file_path: str):
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    
    def _load_scrape_results(self) -> List[Dict]:
        file_path = os.path.join(self.scrape_dir_path, "results.json")
        return self._load_json(file_path)[-2:]

    def _remove_redundant_mace_summary(self, records: List[Dict[str, str]]) -> List[Dict[str, str]]:
        new_records = []
        prev_url = ""
        for record in records:
            if prev_url != "" and prev_url in record["url"]:
                new_records.pop()
            new_records.append(record)
            prev_url = record["url"]
        return new_records
    
    def _save_results(self, data: Union[Dict, List[Dict]], file_path: str, truncate: bool = False, limit: int = 5):
        if isinstance(data, dict):
            if os.path.exists(file_path):
                records = self._load_json(file_path)
                records.append(data)
                if truncate:
                    records = records[-limit:]
            else:
                records = [data]
        elif isinstance(data, list):
            if os.path.exists(file_path):
                records = self._load_json(file_path)
                records.extend(data)
                if truncate:
                    records = records[-limit:]
            else:
                records = data
        self._save_json(records, file_path)
    
    def _save_summary_json(self, data: List[Dict], file_path: str):

        if os.path.exists(file_path):
            records = self._load_json(file_path)
            records.extend(data)
            records = self._remove_redundant_mace_summary(records)
        else:
            records = data
        self._save_json(records, file_path)
    
    def _save_synthesis_json(self, data: Dict[str, str], file_path: str):
        if os.path.exists(file_path):
            records = self._load_json(file_path)
            records.append(data)
        else:
            records = [data]
        self._save_json(records, file_path)
    
    def _save_risk_sentiment_json(self, data: Dict[str, str], file_path: str):
        if os.path.exists(file_path):
            records = self._load_json(file_path)
            records.append(data)
        else:
            records = [data]
        self._save_json(records, file_path)



if __name__ == "__main__":
    pipeline = ProcessPipeline()
    
