from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.actions import router as actions_router
app = FastAPI()
app = FastAPI(title="Hookah CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router, prefix="/api")
app.include_router(actions_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok"}