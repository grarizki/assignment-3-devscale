from app.modules.productDiscovery.router import stories_router
from fastapi import FastAPI

app = FastAPI()

app.include_router(router=stories_router)