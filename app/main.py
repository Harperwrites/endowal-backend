from fastapi import FastAPI

app = FastAPI(title="Endowal API")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
