from chaski.streamer import ChaskiStreamer
from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
import asyncio

app = FastAPI()

streamer = ChaskiStreamer(run=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await streamer.connect('chaski-logger-root-worker', 51114)
    asyncio.create_task(streamer.run())
    yield
    # Shutdown code can go here

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def log(topic, message):
    await streamer.push(topic, message)
    return {"ok": "True"}


import uvicorn
uvicorn.run(app, host="0.0.0.0", port=51115)
