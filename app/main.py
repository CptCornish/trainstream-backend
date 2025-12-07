# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="TrainStream API")

    # CORS so the React frontend (Vite on 5173) can talk to the API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # All our routes (auth, courses, users, venues, participants, templates…)
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
