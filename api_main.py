from fastapi import FastAPI
from fastapi.responses import JSONResponse
from backend.orchestrator.ServerDataLoader import AsyncDataLoader
from typing import Literal

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