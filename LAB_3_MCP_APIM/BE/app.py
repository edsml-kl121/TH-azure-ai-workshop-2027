from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime

app = FastAPI(
    title="Pet Store API",
    description="A simple API to manage pets",
    version="1.0.0"
)

# In-memory storage for pets
pets_db: List[dict] = [
    {"id": 1, "name": "Buddy", "species": "Dog", "age": 3, "created_at": datetime.now().isoformat()},
    {"id": 2, "name": "Whiskers", "species": "Cat", "age": 2, "created_at": datetime.now().isoformat()},
]

# Pydantic models
class PetCreate(BaseModel):
    name: str
    species: str
    age: int

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Max",
                "species": "Dog",
                "age": 5
            }
        }

class Pet(BaseModel):
    id: int
    name: str
    species: str
    age: int
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Max",
                "species": "Dog",
                "age": 5,
                "created_at": "2026-01-16T12:00:00"
            }
        }

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Pet Store API",
        "version": "1.0.0"
    }

@app.get("/pets", response_model=List[Pet])
def get_all_pets():
    """Retrieve all pets"""
    return pets_db

@app.get("/pets/{pet_id}", response_model=Pet)
def get_pet(pet_id: int):
    """Retrieve a specific pet by ID"""
    for pet in pets_db:
        if pet["id"] == pet_id:
            return pet
    raise HTTPException(status_code=404, detail=f"Pet with id {pet_id} not found")

@app.post("/pets", response_model=Pet, status_code=201)
def create_pet(pet: PetCreate):
    """Create a new pet"""
    # Generate new ID
    new_id = max([p["id"] for p in pets_db], default=0) + 1
    
    # Create new pet
    new_pet = {
        "id": new_id,
        "name": pet.name,
        "species": pet.species,
        "age": pet.age,
        "created_at": datetime.now().isoformat()
    }
    
    pets_db.append(new_pet)
    return new_pet

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
