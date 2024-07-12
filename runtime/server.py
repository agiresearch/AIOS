from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/run_agent")
async def run_agent(*args, **kwargs):
    pass

@app.get("/get_all_agents")
async def get_all_agents(*args, **kwargs):
    pass
