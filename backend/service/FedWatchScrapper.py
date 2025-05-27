from backend.service.JinaAIScrapper import JinaAIScrapper
from backend.utils.parameters import FED_WATCH_WEBSITE
from backend.utils.logger_config import get_logger
from backend.agents.fundamental.FedWatchAgent import FedWatchParser, FedWatchData
import aiohttp
import os
import io
from PIL import Image

logger = get_logger(__name__)

class FedWatchScrapper:
    """
    A class to scrape the FedWatch Tool data from the CME Group website.
    """

    def __init__(self):
        self.dir_path = os.path.join("data", "scrape", "fed_watch")
        os.makedirs(self.dir_path, exist_ok=True)
        self.file_path = os.path.join(self.dir_path, "fed_watch.png")

    async def fetch_screen_shot(self, session: aiohttp.ClientSession):
        extract_headers = {
            "X-Return-Format": "pageshot",
            "X-No-Cache": "true",
            "DNT": "1"
        }

        scr = JinaAIScrapper(extra_headers=extract_headers)

        try:
            url = FED_WATCH_WEBSITE
            result = await scr.aget(session, url)
            if result:
                
                img = Image.open(io.BytesIO(result))
                cropped_img = img.crop((0, 1000, img.width, img.height - 4600))  # Adjust crop as needed
                cropped_img.save(self.file_path)
                logger.info(f"FedWatch screenshot saved to {self.file_path}")

        except Exception as e:
            logger.error(f"Error fetching FedWatch data: {e}")
        
    async def parse_screen_shot(self) -> FedWatchData:

        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": 'application/json',
            "response_schema": FedWatchData,
        }

        agent = FedWatchParser(
            chart_path=self.file_path,
            generation_config=generation_config
        )

        result: FedWatchData = await agent.run()
        logger.info(f"FedWatch data parsed")

        return result
    
    async def run(self, session):
        await self.fetch_screen_shot(session=session)
        return await self.parse_screen_shot()


if __name__ == "__main__":
    import asyncio
    scr = FedWatchScrapper()
    result = asyncio.run(scr.parse_screen_shot())

    print(result)

    print(result.model_dump())
    # Example usage
    # raw_data = scr.fetch_screen_shot()
    # parsed_data = scr.parse_screen_shot(raw_data)
    # print(parsed_data)