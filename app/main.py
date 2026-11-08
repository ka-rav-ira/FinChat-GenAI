from fastapi import FastAPI
from app.routers import chat

app = FastAPI(title="Finchat GenAI Backend")

#This tells the main app to load all the routes from chat.py
app.include_router(chat.router)


@app.get("/")
async def home():
    return{"message":"Finchat is running in Modular Mode"}
