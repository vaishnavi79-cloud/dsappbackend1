# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from .database import SessionLocal, engine, Base
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from prophet import Prophet
from datetime import date, timedelta

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Canteen Demand Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/add-entry", response_model=schemas.FoodEntryOut)
def add_entry(entry: schemas.FoodEntryCreate, db: Session = Depends(get_db)):
    # compute wastage
    wastage = round(max(0.0, entry.prepared_qty - entry.consumed_qty), 3)
    db_entry = models.FoodEntry(
        date=entry.date,
        item_name=entry.item_name,
        prepared_qty=entry.prepared_qty,
        consumed_qty=entry.consumed_qty,
        wastage=wastage
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@app.get("/history", response_model=list[schemas.FoodEntryOut])
def get_history(item_name: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.FoodEntry)
    if item_name:
        q = q.filter(models.FoodEntry.item_name == item_name)
    return q.order_by(models.FoodEntry.date.desc()).limit(500).all()

@app.get("/wastage-summary")
def wastage_summary(db: Session = Depends(get_db)):
    q = db.query(models.FoodEntry).all()
    if not q:
        return {"message": "no data", "total_wastage": 0.0}
    df = pd.DataFrame([{
        "date": r.date,
        "item": r.item_name,
        "wastage": r.wastage
    } for r in q])
    total_wastage = float(df['wastage'].sum())
    by_item = df.groupby('item')['wastage'].sum().sort_values(ascending=False).to_dict()
    weekly = df.groupby(pd.Grouper(key='date', freq='W'))['wastage'].sum().reset_index().to_dict(orient='records')
    return {"total_wastage": total_wastage, "by_item": by_item, "weekly": weekly}

@app.get("/predict")
def predict(item_name: str | None = None, days: int = 1, db: Session = Depends(get_db)):
    # Build dataframe of historical consumption grouped by date (for the item or overall)
    q = db.query(models.FoodEntry)
    if item_name:
        q = q.filter(models.FoodEntry.item_name == item_name)
    rows = q.order_by(models.FoodEntry.date).all()
    if len(rows) < 10:
        raise HTTPException(status_code=400, detail="Not enough data to forecast (need >=10 rows)")

    df = pd.DataFrame([{"ds": r.date, "y": float(r.consumed_qty)} for r in rows])
    df = df.groupby("ds").sum().reset_index()
    # Prophet expects ds (datetime) and y
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=days)
    forecast = model.predict(future)
    res = forecast[['ds','yhat','yhat_lower','yhat_upper']].tail(days).to_dict(orient='records')
    # round numbers
    for r in res:
        r['yhat'] = round(float(r['yhat']),3)
        r['yhat_lower'] = round(float(r['yhat_lower']),3)
        r['yhat_upper'] = round(float(r['yhat_upper']),3)
        r['ds'] = r['ds'].isoformat()
    return {"forecast": res}
