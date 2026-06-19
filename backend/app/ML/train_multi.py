import os
import joblib
import warnings
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier

from app.ML.features import get_user_history, parse_sleep, safe_map, _ENERGY_MAP, _PHASE_MAP, _MOOD_CAT_MAP, _MOOD_DETAIL_MAP
from app.core.db import SessionLocal
from app.models.user import User

OUT_PATH = os.path.join(os.path.dirname(__file__), "model_multi.joblib")


def build_supervised_for_user(df: pd.DataFrame, window: int = 3):
    if df.empty or len(df) < window + 1:
        return pd.DataFrame(), pd.Series(dtype=int), pd.Series(dtype=int)

    df_rev = df.iloc[::-1].reset_index(drop=True)
    rows = []
    labels_energy = []
    labels_mood = []

    for i in range(window, len(df_rev)):
        recent = df_rev.iloc[i - window: i]
        target = df_rev.iloc[i]

        feat: dict = {}

        feat["hist_mean_sleep"] = float(recent["sleep"].dropna().astype(float).mean()) if "sleep" in recent else np.nan
        energy_vals = recent["energy"].map(lambda x: safe_map(x, _ENERGY_MAP, default=np.nan)) if "energy" in recent else np.nan
        feat["hist_mean_energy"] = float(energy_vals.dropna().mean()) if not energy_vals.dropna().empty else np.nan
        feat["hist_mood_variety"] = float(recent.get("mood_detail", pd.Series(dtype=object)).nunique()) if "mood_detail" in recent else 0.0

        last = recent.iloc[-1]
        feat["last_energy"] = safe_map(last.get("energy"), _ENERGY_MAP, default=-1)
        feat["last_mood_cat"] = safe_map(last.get("mood_category") or last.get("mood"), _MOOD_CAT_MAP, default=-1)
        feat["last_mood_detail"] = safe_map(last.get("mood_detail"), _MOOD_DETAIL_MAP, default=-1)
        feat["last_phase"] = safe_map(last.get("cycle_phase"), _PHASE_MAP, default=-1)

        total = len(recent)
        phase_series = recent["cycle_phase"].fillna("unknown").map(lambda v: str(v).strip().lower())
        for ph in _PHASE_MAP.keys():
            feat[f"hist_phase_pct_{ph}"] = float((phase_series == ph).sum()) / total if total > 0 else 0.0

        # multiclass energy label (0=low, 1=medium, 2=high)
        target_energy = safe_map(target.get("energy"), _ENERGY_MAP, default=-1)
        labels_energy.append(int(target_energy) if target_energy >= 0 else -1)

        target_mood_cat = safe_map(target.get("mood_category") or target.get("mood"), _MOOD_CAT_MAP, default=-1)
        labels_mood.append(int(target_mood_cat) if target_mood_cat >= 0 else -1)

        rows.append(feat)

    X = pd.DataFrame(rows)
    y_energy = pd.Series(labels_energy)
    y_mood = pd.Series(labels_mood)

    # filter out rows where mood label is invalid (-1)
    valid_m = y_mood >= 0
    if not valid_m.all():
        X = X[valid_m.values].reset_index(drop=True)
        y_energy = y_energy[valid_m.values].reset_index(drop=True)
        y_mood = y_mood[valid_m.values].reset_index(drop=True)

    # filter out rows where energy label is invalid (-1)
    valid_e = y_energy >= 0
    if not valid_e.all():
        X = X[valid_e.values].reset_index(drop=True)
        y_energy = y_energy[valid_e.values].reset_index(drop=True)
        y_mood = y_mood[valid_e.values].reset_index(drop=True)

    return X, y_energy, y_mood


def get_all_user_ids(db):
    return [u.id for u in db.query(User).all()]


def build_dataset(db, window: int = 3):
    X_list = []
    y_energy_list = []
    y_mood_list = []
    for uid in get_all_user_ids(db):
        df = get_user_history(db, uid, limit=1000)
        if df.empty:
            continue
        X_u, y_e_u, y_m_u = build_supervised_for_user(df, window=window)
        if not X_u.empty:
            X_list.append(X_u)
            y_energy_list.append(y_e_u)
            y_mood_list.append(y_m_u)
    if not X_list:
        return pd.DataFrame(), pd.Series(dtype=int), pd.Series(dtype=int)
    X_all = pd.concat(X_list, ignore_index=True).fillna(0)
    y_energy_all = pd.concat(y_energy_list, ignore_index=True)
    y_mood_all = pd.concat(y_mood_list, ignore_index=True)

    # debug: show dataset summary so we can see how many classes are present
    try:
        print("Dataset assembled:", X_all.shape)
        print("Energy label counts:\n", y_energy_all.value_counts(dropna=False).to_dict())
        print("Mood label counts:\n", y_mood_all.value_counts(dropna=False).to_dict())
        if "last_energy" in X_all.columns:
            print("last_energy distribution:\n", X_all["last_energy"].value_counts(dropna=False).to_dict())
        if "hist_mean_energy" in X_all.columns:
            print("hist_mean_energy stats: mean=", float(X_all["hist_mean_energy"].mean()), "min=", float(X_all["hist_mean_energy"].min()), "max=", float(X_all["hist_mean_energy"].max()))
    except Exception as _e:
        print("Failed to print dataset debug info:", _e)

    return X_all, y_energy_all, y_mood_all


def _safe_train_test_split(X, y, test_size=0.2, random_state=42):
    vc = Counter(y)
    n_samples = len(y)
    n_classes = len(vc)
    if n_samples == 0 or n_classes == 0:
        raise ValueError("Empty label vector for splitting.")

    # compute integer number of test samples we would get
    if isinstance(test_size, float):
        n_test = max(1, int(round(n_samples * test_size)))
    else:
        n_test = int(test_size)

    # require at least one test sample per class and at least two samples per class for stratify
    if n_test >= n_classes and min(vc.values()) >= 2:
        return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
    else:
        warnings.warn(
            "Not enough samples per class or test set too small for stratified split; using non-stratified split."
        )
        return train_test_split(X, y, test_size=test_size, random_state=random_state)


def _dummy_with_all_classes(X, y, all_classes):
    """Fit a DummyClassifier that knows about all classes even if not present in y.
    Append one example per desired class so X_aug and y_aug lengths match.
    """
    clf = DummyClassifier(strategy="most_frequent")
    # ensure there's at least one row to duplicate; if not, create a zero-row with correct columns
    if len(X) == 0:
        # create single zero row matching column names (unlikely since caller checks X.empty)
        first_row = pd.DataFrame([[0] * len(X.columns)], columns=X.columns)
    else:
        first_row = X.iloc[:1].copy()

    # append one exemplar per class so the classifier's classes_ includes all_classes
    extras = [first_row] * len(all_classes)
    X_aug = pd.concat([X, *extras], ignore_index=True)
    y_aug = pd.concat([y, pd.Series(all_classes, dtype=y.dtype)], ignore_index=True)
    clf.fit(X_aug, y_aug)
    return clf


def train_and_save(window: int = 3):
    db = SessionLocal()
    try:
        X, y_energy, y_mood = build_dataset(db, window=window)
        if X.empty:
            print("No data to train on.")
            return

        # debug: print a clear summary before training
        try:
            print("Training dataset shape:", X.shape)
            print("Energy value counts (pre-train):", y_energy.value_counts().to_dict())
            print("Mood value counts (pre-train):", y_mood.value_counts().to_dict())
            # show unique mapped energy labels that exist
            if "last_energy" in X.columns:
                print("last_energy unique:", sorted(X["last_energy"].unique()))
        except Exception as _e:
            print("Failed to print pre-train debug info:", _e)
        
        feature_cols = list(X.columns)
        models = {}

        # --- Energy model (multiclass: 0=low, 1=medium, 2=high) ---
        vc_energy = Counter(y_energy)
        ALL_ENERGY_CLASSES = [0, 1, 2]
        if len(vc_energy) == 0:
            # no energy labels at all
            print("Energy: no labeled samples — using fallback dummy classifier")
            models["energy"] = _dummy_with_all_classes(X, y_energy, all_classes=ALL_ENERGY_CLASSES)
        else:
            # if some classes are missing, append one synthetic sample per missing class
            missing = [c for c in ALL_ENERGY_CLASSES if c not in vc_energy]
            X_for_energy = X.copy()
            y_for_energy = y_energy.copy()
            if missing:
                print(f"Energy: missing classes {missing} — appending {len(missing)} synthetic samples (column means) so model has all classes.")
                mean_row = X_for_energy.mean(axis=0)
                synth_rows = pd.DataFrame([mean_row.values] * len(missing), columns=X_for_energy.columns)
                X_for_energy = pd.concat([X_for_energy, synth_rows], ignore_index=True)
                y_for_energy = pd.concat([y_for_energy, pd.Series(missing, dtype=y_for_energy.dtype)], ignore_index=True)
                # show counts after augmentation
                print("Energy value counts (after synth augment):", y_for_energy.value_counts().to_dict())
            try:
                X_tr, X_te, y_tr, y_te = _safe_train_test_split(X_for_energy, y_for_energy)
                clf_e = RandomForestClassifier(n_estimators=100, random_state=42)
                clf_e.fit(X_tr, y_tr)
                if len(Counter(y_te)) > 1:
                    print("Energy AUC:", roc_auc_score(
                        y_te,
                        clf_e.predict_proba(X_te),
                        multi_class='ovr',
                        average='macro'
                    ))
                print("Energy Classification Report:")
                print(classification_report(y_te, clf_e.predict(X_te)))
                models["energy"] = clf_e
            except Exception as e:
                print(f"Energy model training failed: {e}")
                models["energy"] = _dummy_with_all_classes(X, y_energy, all_classes=ALL_ENERGY_CLASSES)

        # --- Mood model (multiclass: 0=negative, 1=neutral, 2=positive) ---
        ALL_MOOD_CLASSES = [0, 1, 2]
        vc_mood = Counter(y_mood)
        if len(vc_mood) == 0:
            print("Mood: no labeled samples — using fallback dummy classifier")
            models["mood"] = _dummy_with_all_classes(X, y_mood, all_classes=ALL_MOOD_CLASSES)
        else:
            missing_m = [c for c in ALL_MOOD_CLASSES if c not in vc_mood]
            X_for_mood = X.copy()
            y_for_mood = y_mood.copy()
            if missing_m:
                print(f"Mood: missing classes {missing_m} — appending {len(missing_m)} synthetic samples (column means) so model has all classes.")
                mean_row = X_for_mood.mean(axis=0)
                synth_rows = pd.DataFrame([mean_row.values] * len(missing_m), columns=X_for_mood.columns)
                X_for_mood = pd.concat([X_for_mood, synth_rows], ignore_index=True)
                y_for_mood = pd.concat([y_for_mood, pd.Series(missing_m, dtype=y_for_mood.dtype)], ignore_index=True)
                print("Mood value counts (after synth augment):", y_for_mood.value_counts().to_dict())
            try:
                X_tr, X_te, y_tr, y_te = _safe_train_test_split(X_for_mood, y_for_mood)
                clf_m = RandomForestClassifier(n_estimators=100, random_state=42)
                clf_m.fit(X_tr, y_tr)
                print("Mood Classification Report:")
                print(classification_report(y_te, clf_m.predict(X_te)))
                models["mood"] = clf_m
            except Exception as e:
                print(f"Mood model training failed: {e}")
                models["mood"] = _dummy_with_all_classes(X, y_mood, all_classes=ALL_MOOD_CLASSES)

        bundle = {"models": models, "feature_cols": feature_cols}
        joblib.dump(bundle, OUT_PATH)
        print(f"Saved model bundle to {OUT_PATH}")

    finally:
        db.close()


if __name__ == "__main__":
    train_and_save(window=3)