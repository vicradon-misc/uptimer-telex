from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List
import httpx

app = FastAPI()


@app.get("/integration.json")
def get_integration_json():
    integration_json = {
        "data": {
            "date": {"created_at": "2025-02-09", "updated_at": "2025-02-09"},
            "descriptions": {
                "app_name": "Uptime Monitor",
                "app_description": "An uptime monitor",
                "app_logo": '"https://st2.depositphotos.com/42585882/42219/i/450/depositphotos_422190474-stock-photo-unique-logo-design-shape.jpg',
                "app_url": "https://uptime-monitor.osinachi.me",
                "background_color": "#fff",
            },
            "is_active": true,
            "integration_type": "checkbox",
            "key_features": ["- monitors websites"],
            "author": "Osinachi Chukwujama",
            "settings": [
                {"label": "site-1", "type": "text", "required": true, "default": ""},
                {"label": "site-2", "type": "text", "required": true, "default": ""},
                {
                    "label": "interval",
                    "type": "text",
                    "required": true,
                    "default": "* * * * *",
                },
            ],
            "target_url": "https://8000-vicradon-gitpodpg-z0k09klhibl.ws-eu117.gitpod.io/target",
            "tick_url": "https://8000-vicradon-gitpodpg-z0k09klhibl.ws-eu117.gitpod.io/tick",
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

    telex_format = {
        channel_id: payload.channel_id,
        message: results
    }

    # Send results to external webhook
    async with httpx.AsyncClient() as client:
        await client.post(f"https://ping.telex.im/return/{payload.channel_id}", json=results)


@app.post("/tick", status_code=202)
def monitor(payload: MonitorPayload, background_tasks: BackgroundTasks):
    """Immediately returns 202 and runs monitoring in the background."""
    background_tasks.add_task(monitor_task, payload)
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
