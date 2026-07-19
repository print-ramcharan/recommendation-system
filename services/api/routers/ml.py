import os
import json
import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ml.training.main import run_pipeline

router = APIRouter(prefix="/ml", tags=["ml"])

STATUS_FILE = "ml/training/checkpoints/status.json"

def get_status_payload():
    if not os.path.exists(STATUS_FILE):
        return {
            "status": "idle",
            "epoch": 0,
            "total_epochs": 5,
            "train_loss": 0.0,
            "val_loss": 0.0,
            "message": "Model has not been trained yet."
        }
    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        return {
            "status": "idle",
            "epoch": 0,
            "total_epochs": 5,
            "train_loss": 0.0,
            "val_loss": 0.0,
            "message": f"Error loading status file: {e}"
        }

def save_status_payload(payload):
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(payload, f)

async def async_training_worker():
    try:
        await run_pipeline()
    except Exception as e:
        save_status_payload({
            "status": "failed",
            "epoch": 0,
            "total_epochs": 5,
            "train_loss": 0.0,
            "val_loss": 0.0,
            "message": f"Training failed: {str(e)}"
        })

@router.post("/train")
async def trigger_ncf_training(background_tasks: BackgroundTasks):
    current_status = get_status_payload().get("status")
    if current_status == "training":
        raise HTTPException(status_code=409, detail="NCF model training is already in progress.")
        
    save_status_payload({
        "status": "training",
        "epoch": 0,
        "total_epochs": 5,
        "train_loss": 0.0,
        "val_loss": 0.0,
        "message": "Initializing training pipeline dataset..."
    })
    background_tasks.add_task(async_training_worker)
    return {"message": "NCF model training pipeline triggered in background."}

@router.get("/status")
async def get_ncf_training_status():
    return get_status_payload()
