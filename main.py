from fastapi import FastAPI
from app.database.db import engine
from dotenv import load_dotenv

load_dotenv()

# Import models
from app.models.doctor import Doctor
from app.api.doctor_routes import router as doctor_router
from app.api.appointment_routes import router as appointment_router
from app.api.call_routes import router as call_router



app = FastAPI()

app.include_router(doctor_router)
app.include_router(appointment_router)
app.include_router(call_router)

@app.get("/")
def home():
    return {"message": "AI Doctor Agent Running"}