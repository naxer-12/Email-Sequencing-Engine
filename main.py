from fastapi import FastAPI
from pydantic import BaseModel

from config import settings

app = FastAPI(title="Email Engine")

DATABASE_URL = settings.database_url


class Sequence(BaseModel):
    name: str
    status: str = "draft"


@app.get("/")
async def root():
    return {"message": "Email engine checked"}


@app.get("/sequences/{sequence_id}")
async def get_sequence(sequence_id: int):
    return {"id": sequence_id, "name": f"Sequence {sequence_id}"}


@app.post("/sequences")
async def create_sequence(seq: Sequence):
    return {"created": seq.name, "status": seq.status}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
