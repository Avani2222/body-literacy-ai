from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.models.user_data import UserData

# --- encoders aligned with your Dashboard choices ---
_PHASE_MAP = {"menstrual": 0, "follicular": 1, "ovulatory": 2, "luteal": 3}

_MOOD_DETAIL_MAP = {
    # positive
    "happy": 2, "energetic": 2, "motivated": 2, "confident": 2, "relaxed": 2,
    # neutral
    "calm": 1, "okay": 1, "tired": 1, "numb": 1, "meh": 1,
    # negative
    "anxious": 0, "stressed": 0, "sad": 0, "irritated": 0, "overwhelmed": 0,
}

_MOOD_CAT_MAP = {"positive": 2, "neutral": 1, "negative": 0}
_ENERGY_MAP = {"low": 0, "medium": 1, "high": 2}


def parse_sleep(s: Optional[Any]) -> Optional[float]:
    if s is None:
        return None
    try:
        return float(s)
    except Exception:
        try:
            return float(str(s).strip())
        except Exception:
            return None

def safe_map(value: Optional[Any], mapping: Dict[str, int], default: int = -1) -> int:
    if value is None:
        return default
    return mapping.get(str(value).lower(), default)

def get_user_history(db: Session, user_id: Any, limit: int = 50) -> pd.DataFrame:
    uid = str(user_id)
    rows = (
        db.query(UserData)
        .filter(UserData.user_id == uid)
        .order_by(UserData.id.desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return pd.DataFrame(columns=["cycle_phase", "mood_category", "mood_detail", "energy", "sleep"])
    
    data = []
    for r in rows:
        mood_raw = getattr(r, "mood", None)
        mood_cat = getattr(r, "mood_category", None)
        mood_detail = getattr(r, "mood_detail", None)
        if mood_cat is None and mood_detail is None and mood_raw is not None:
            m = str(mood_raw).strip().lower()
            if m in _MOOD_DETAIL_MAP:
                mood_detail = mood_raw
                val = _MOOD_DETAIL_MAP[m]
                mood_cat = "positive" if val == 2 else ("neutral" if val == 1 else "negative")
            else:
                mood_detail = mood_raw
                mood_cat = None
        data.append({
            "cycle_phase": getattr(r, "cycle_phase", None),
            "mood_category": mood_cat,
            "mood_detail": mood_detail,
            "energy": getattr(r, "energy", None),
            "sleep": parse_sleep(getattr(r, "sleep", None)),
        })
    return pd.DataFrame(data)

def compute_history_aggregates(df: pd.DataFrame) -> Dict[str, Any]:
    out: Dict[str, float] = {}
    if df.empty:
        out.update({
            "hist_count": 0,
            "hist_mean_sleep": float("nan"),
            "hist_mean_energy": float("nan"),
            "hist_mood_cat_pos_pct": 0.0,
            "hist_mood_cat_neu_pct": 0.0,
            "hist_mood_cat_neg_pct": 0.0,
            "hist_mood_detail_variety": 0.0,
        })
        for ph in _PHASE_MAP.keys():
            out[f"hist_phase_pct_{ph}"] = 0.0
        return out
    
    total = len(df)
    out["hist_count"] = total
    out["hist_mean_sleep"] = float(df["sleep"].dropna().mean()) if "sleep" in df else float("nan")

    energy_vals = df["energy"].map(lambda x: safe_map(x, _ENERGY_MAP, default=np.nan)) if "energy" in df else pd.Series(dtype=float)
    out["hist_mean_energy"] = float(energy_vals.dropna().mean()) if not energy_vals.dropna().empty else float("nan")

    cat_series = df["mood_category"].fillna("unknown").map(lambda v: str(v).strip().lower())
    out["hist_mood_cat_pos_pct"] = float((cat_series == "positive").sum()) / total
    out["hist_mood_cat_neu_pct"] = float((cat_series == "neutral").sum()) / total
    out["hist_mood_cat_neg_pct"] = float((cat_series == "negative").sum()) / total  

    out["hist_mood_detail_variety"] = float(df["mood_detail"].nunique()) if "mood_detail" in df else 0.0

    phase_series = df["cycle_phase"].fillna("unknown").map(lambda v: str(v).strip().lower())
    for ph in _PHASE_MAP.keys():
        out[f"hist_phase_pct_{ph}"] = float((phase_series == ph).sum()) / total if total > 0 else 0.0
    return out

def make_feature_vector(data: Dict[str, Any], db: Session, history_length: int = 20) -> pd.DataFrame:
    user_id = data.get("user_id")

    hist_df = get_user_history(db, user_id, limit=history_length)

    # Need at least 1 row to form a "last" row + some history
    if hist_df.empty:
        return pd.DataFrame()  # triggers 400 in endpoint

    window = min(3, len(hist_df))
    recent = hist_df.iloc[:window]   # most recent N rows
    last = recent.iloc[0]            # most recent single row

    features: Dict[str, Any] = {}

    features["hist_mean_sleep"] = float(
        recent["sleep"].dropna().astype(float).mean()
    ) if not recent["sleep"].dropna().empty else np.nan

    energy_vals = recent["energy"].map(
        lambda x: safe_map(x, _ENERGY_MAP, default=np.nan)
    )
    features["hist_mean_energy"] = float(
        energy_vals.dropna().mean()
    ) if not energy_vals.dropna().empty else np.nan

    features["hist_mood_variety"] = float(
        recent["mood_detail"].nunique()
    ) if "mood_detail" in recent else 0.0

    features["last_energy"] = safe_map(
        data.get("energy") or last.get("energy"), _ENERGY_MAP, default=-1
    )
    features["last_mood_cat"] = safe_map(
        data.get("mood_category") or data.get("mood") or last.get("mood_category"),
        _MOOD_CAT_MAP, default=-1
    )
    features["last_mood_detail"] = safe_map(
        data.get("mood_detail") or last.get("mood_detail"), _MOOD_DETAIL_MAP, default=-1
    )
    features["last_phase"] = safe_map(
        data.get("cycle_phase") or last.get("cycle_phase"), _PHASE_MAP, default=-1
    )

    total = len(recent)
    phase_series = recent["cycle_phase"].fillna("unknown").map(
        lambda v: str(v).strip().lower()
    )
    for ph in _PHASE_MAP.keys():
        features[f"hist_phase_pct_{ph}"] = (
            float((phase_series == ph).sum()) / total if total > 0 else 0.0
        )

    features["user_id"] = str(user_id) if user_id else "unknown"

    return pd.DataFrame([features])

def feature_vector_to_numpy(df: pd.DataFrame, drop_cols: Optional[List[str]] = None) -> Tuple[np.ndarray, List[str]]:
    if drop_cols is None:
        drop_cols = ["user_id"]
    feature_cols = [c for c in df.columns if c not in drop_cols]
    arr = df[feature_cols].fillna(0.0).to_numpy(dtype=float)
    return arr, feature_cols

__all__ = [
    "parse_sleep",
    "get_user_history",
    "compute_history_aggregates",
    "make_feature_vector",
    "feature_vector_to_numpy",
]