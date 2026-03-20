import uvicorn

if name == "__main__":
    uvicorn.run("app.web.auth_api:app", host="127.0.0.1", port=8001, reload=False)