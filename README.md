# Backend - Canteen Demand Predictor API

## Setup (recommended virtualenv)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

## Run
uvicorn app.main:app --reload --port 8000

## Endpoints
POST /add-entry  (json: date (YYYY-MM-DD), item_name, prepared_qty, consumed_qty)
GET /history
GET /wastage-summary
GET /predict?item_name=Rice&days=2
