import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://staging.telextest.im", "http://telextest.im", "https://staging.telex.im", "https://telex.im"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

@app.get("/logo")
def get_logo():
    return FileResponse("uptime.png")

@app.get("/integration.json")
def get_integration_json():
    integration_json = {
        "data": {
            "date": {"created_at": "2025-02-09", "updated_at": "2025-02-09"},
            "descriptions": {
                "app_name": "Uptime Monitor",
                "app_description": "A local uptime monitor",
                "app_logo": "https://i.imgur.com/lZqvffp.png",
                "app_url": "http://localhost:8000"
                "background_color": "#fff",
            },
            "is_active": False,
            "integration_type": "interval",
            "key_features": ["- monitors websites"],
            "author": "Osinachi Chukwujama",
            "website": "http://localhost:8000"
            "settings": [
                {"label": "site-1", "type": "text", "required": True, "default": ""},
                {"label": "site-2", "type": "text", "required": True, "default": ""},
                {
                    "label": "interval",
                    "type": "text",
                    "required": True,
                    "default": "* * * * *",
                },
            ],
            "target_url": ""
            "tick_url": "http://localhost:8000/tick"
        }
    }

    return integration_json


async def check_site_status(site: str):
    """Check if a site is up or down."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(site)
            status = "up" if response.status_code == 200 else "down"
    except Exception:
        status = "down"

    return {"site": site, "status": status}


class Setting(BaseModel):
    label: str
    type: str
    required: bool
    default: str


class MonitorPayload(BaseModel):
    channel_id: str
    settings: List[Setting]


async def monitor_task(payload: MonitorPayload):
    """Background task to monitor sites and send results."""
    sites = []

    for setting in payload.settings:
        if setting.label.startswith("site"):
            sites.append(setting.default)

    results = await asyncio.gather(*(check_site_status(site) for site in sites))

    telex_format = {"channel_id": payload.channel_id, "message": results}

    # Send results to external webhook
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://ping.telex.im/return/{payload.channel_id}", json=results
        )


@app.post("/tick", status_code=202)
def monitor(payload: MonitorPayload, background_tasks: BackgroundTasks):
    """Immediately returns 202 and runs monitoring in the background."""
    background_tasks.add_task(monitor_task, payload)
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
