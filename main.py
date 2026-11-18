import uuid

from fastapi import FastAPI
import redis
import redis.asyncio as aioredis
from fastapi import WebSocket
from fastapi.responses import FileResponse

app = FastAPI()
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
ar = aioredis.Redis(host="localhost", port=6379, decode_responses=True)


@app.websocket("/ws/jobs/{job_id}")
async def jobs(websocket: WebSocket, job_id: str):
    await websocket.accept()
    pubsub = ar.pubsub()
    await pubsub.subscribe(f"progress:{job_id}")
    current = await ar.get(f"progress:{job_id}")
    if current is not None:
        await websocket.send_text(current)
    async for message in pubsub.listen():
        if message["type"] == "message":
            await websocket.send_text(message["data"])
            if message["data"] == "100":
                break
    await websocket.close()


@app.post("/jobs", status_code=202)
def create_job():
    new_id = str(uuid.uuid4())
    r.lpush("jobs", new_id)
    return {"job_id": new_id}


@app.get("/")
def home():
    return FileResponse("index.html")
