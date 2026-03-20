from fastapi import FastAPI
import uvicorn

from app.api.routes.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(
        "run_api:app",
        host="0.0.0.0",
        port=8000
    )