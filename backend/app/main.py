from fastapi import FastAPI
from app.api import routes_ai, routes_auth
from fastapi.middleware.cors import CORSMiddleware
from app.core.db import engine
from app.models import user_data, user  # import your models
from app.core.db import Base
from app.api import routes_ml


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(routes_ai.router)
app.include_router(routes_auth.router)
app.include_router(routes_ml.router)
for route in app.routes:
    print(route.path, route.methods)
Base.metadata.create_all(bind=engine)
@app.get("/")
def home():
    return {"message": "Body Literacy AI running"}

