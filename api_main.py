from fastapi import FastAPI
from fastapi.responses import JSONResponse
from backend.orchestrator.ServerDataLoader import AsyncDataLoader
from typing import Literal
import asyncio, contextlib, logging
from backend.utils.logger_config import get_logger
logger = get_logger(__name__)
import server_main



app = FastAPI()
data_loader = AsyncDataLoader()

@app.get("/news_synthesis/{currency_pair}")
async def news_synthesis(currency_pair: Literal["eur_usd", "gbp_usd", "usd_jpy", "usd_cnh"]):
    data = await data_loader.get_news_synthesis(currency_pair)
    return JSONResponse(content=data)

@app.get("/calendar_synthesis/{currency_pair}")
async def calendar_synthesis(currency_pair: str):
    data = await data_loader.get_calender_synthesis(currency_pair)
    return JSONResponse(content=data)

@app.get("/fedwatch_synthesis")
async def fedwatch_synthesis():
    data = await data_loader.get_fedwatch_synthesis()
    return JSONResponse(content=data)

@app.get("/fundamental_synthesis/{currency_pair}")
async def fundamental_synthesis(currency_pair: str):
    data = await data_loader.get_fundamental_synthesis(currency_pair)
    return JSONResponse(content=data)

@app.get("/risk_sentiment_synthesis/{currency_pair}")
async def risk_sentiment_synthesis(currency_pair: str):
    data = await data_loader.get_risk_sentiment_synthesis(currency_pair)
    return JSONResponse(content=data)

@app.get("/scrape_results")
async def scrape_results():
    data = await data_loader.get_scrape_results()
    return JSONResponse(content=data)

_background_task: asyncio.Task | None = None
log = logging.getLogger("uvicorn.error")

@app.on_event("startup")
async def start_background_scraper() -> None:
    """
    Kick off one long-lived asyncio.Task that runs the pipelines every 30 min.
    """
    async def _loop() -> None:
        while True:
            try:
                await server_main.run_once()
            except Exception:
                log.exception("Background pipeline run failed")
            # Sleep *after* the run so the first run starts immediately
            await asyncio.sleep(30 * 60)   # 30 minutes

    global _background_task
    _background_task = asyncio.create_task(_loop())
    log.info("Background scraper started")

@app.on_event("shutdown")
async def stop_background_scraper() -> None:
    """
    Cancel the background task gracefully when uvicorn stops.
    """
    if _background_task:
        _background_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _background_task
        log.info("Background scraper stopped")