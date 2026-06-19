from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import joblib
import os
from typing import Optional, Any, Dict, Union
import numpy as np
import threading

from app.core.db import SessionLocal
from app.ML.features import make_feature_vector
from app.ML import train_multi

router = APIRouter(prefix="/ml", tags=["ml"])

_ENERGY_LABELS = {0: "low", 1: "medium", 2: "high"}
_MOOD_LABELS = {0: "negative", 1: "neutral", 2: "positive"}

MODEL_MULTI = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ML", "model_multi.joblib"))
MODEL_SINGLE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ML", "model.joblib"))
_bundle = None
_train_lock = threading.Lock()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def load_bundle(force: bool = False):
    global _bundle
    if _bundle is None or force:
        if os.path.exists(MODEL_MULTI):
            _bundle = joblib.load(MODEL_MULTI)
        elif os.path.exists(MODEL_SINGLE):
            _bundle = joblib.load(MODEL_SINGLE)
        else:
            _bundle = None
    return _bundle


class PredictRequest(BaseModel):
    user_id: Optional[str] = None
    cycle_phase: str
    mood: Optional[str] = None
    mood_category: Optional[str] = None
    mood_detail: Optional[str] = None
    energy: Optional[str] = None
    sleep: Optional[Union[str, float]] = None


def _run_prediction(models, feature_cols, payload, db):
    """Build feature vector and run both models. Returns preds dict."""
    fv = make_feature_vector(payload, db, history_length=3)
    if fv is None or fv.empty:
        raise HTTPException(
            status_code=400,
            detail="Could not build feature vector — no user history found"
        )

    feat_dict = fv.iloc[0].to_dict()
    X_df = fv.drop(columns=["user_id"]) if "user_id" in fv.columns else fv.copy()

    if feature_cols:
        missing = [c for c in feature_cols if c not in X_df.columns]
        if missing:
            raise HTTPException(
                status_code=500,
                detail=f"Missing features: {missing}"
            )
        X_df = X_df[feature_cols]

    try:
        X_np = X_df.fillna(0.0).to_numpy(dtype=float)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature conversion error: {e}")

    preds: Dict[str, Any] = {}

    # energy
    if models and "energy" in models:
        try:
            m = models["energy"]
            proba_arr = m.predict_proba(X_np)[0]
            classes = list(m.classes_)
            pred_class = int(m.predict(X_np)[0])
            preds["energy"] = {
                "prediction": _ENERGY_LABELS.get(pred_class, str(pred_class)),
                "confidence": f"{round(max(proba_arr) * 100)}%",
                "probabilities": {
                    _ENERGY_LABELS.get(int(classes[i]), str(classes[i])): f"{round(float(proba_arr[i]) * 100)}%"
                    for i in range(len(classes))
                }
            }
        except Exception as e:
            preds["energy"] = {"error": str(e)}
    else:
        preds["energy"] = {"warning": "no energy model in bundle"}

    # mood
    if models and "mood" in models:
        try:
            m = models["mood"]
            proba_arr = m.predict_proba(X_np)[0]
            classes = list(m.classes_)
            pred_class = int(m.predict(X_np)[0])
            preds["mood"] = {
                "prediction": _MOOD_LABELS.get(pred_class, str(pred_class)),
                "confidence": f"{round(max(proba_arr) * 100)}%",
                "probabilities": {
                    _MOOD_LABELS.get(int(classes[i]), str(classes[i])): f"{round(float(proba_arr[i]) * 100)}%"
                    for i in range(len(classes))
                }
            }
        except Exception as e:
            preds["mood"] = {"error": str(e)}
    else:
        preds["mood"] = {"warning": "no mood model in bundle"}

    features_out = {
        k: (float(v) if isinstance(v, (int, float, np.integer, np.floating)) else v)
        for k, v in feat_dict.items()
    }

    return preds, features_out, list(X_df.columns)


@router.post("/predict")
def predict(request: PredictRequest, db: Session = Depends(get_db)):
    global _bundle

    bundle = load_bundle()
    if bundle is None:
        acquired = _train_lock.acquire(blocking=False)
        try:
            if acquired:
                train_multi.train_and_save(window=3)
            else:
                with _train_lock:
                    pass
        finally:
            if acquired:
                _train_lock.release()
        bundle = load_bundle(force=True)  # force reload after training

    if bundle is None:
        raise HTTPException(status_code=500, detail="Model training failed or no data available")

    payload = request.dict()
    if payload.get("sleep") is not None and not isinstance(payload["sleep"], str):
        payload["sleep"] = str(payload["sleep"])
    if not payload.get("mood"):
        payload["mood"] = payload.get("mood_detail") or payload.get("mood_category")

    models = bundle.get("models") or bundle.get("model")
    feature_cols = bundle.get("feature_cols") or bundle.get("feature_names")

    preds, features_out, feature_names = _run_prediction(models, feature_cols, payload, db)
    return {"predictions": preds, "features": features_out, "feature_names": feature_names}


@router.post("/retrain")
def retrain():
    global _bundle
    _bundle = None  # clear cache
    train_multi.train_and_save(window=3)
    bundle = load_bundle(force=True)
    if bundle is None:
        raise HTTPException(status_code=500, detail="Training failed — check logs")
    return {
        "status": "ok",
        "models": list(bundle.get("models", {}).keys()),
        "feature_cols": bundle.get("feature_cols", [])
    }