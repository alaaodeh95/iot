import os
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from backend.models import ActuatorCommand

logger = logging.getLogger(__name__)


class MLModelManager:
    """
    ML manager for actuator decision support with basic lifecycle:
    - train with recent data (and synthetic fallback)
    - versioning metadata
    - simple drift check on recent window
    """

    def __init__(self, db, model_path: str = "./model_store/hvac_model.pkl"):
        self.db = db
        self.model_path = model_path
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        self.model = None
        self.label_map = {0: "off", 1: "fan_only", 2: "cooling", 3: "heating"}
        self.status: Dict[str, Any] = {
            "loaded": False,
            "last_trained": None,
            "samples": 0,
            "features": ["temperature", "humidity", "co2"],
            "algorithm": "RandomForestClassifier",
            "f1": None,
            "version": 0,
            "training_window_hours": 168,
            "drift_score": None,
            "drift_checked_at": None,
            "next_retrain_at": None,
            "baseline_stats": None,
        }
        self._load()

    def _load(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.status["loaded"] = True
                logger.info("ML model loaded from %s", self.model_path)
            except Exception as exc:
                logger.error("Failed to load model: %s", exc)
                self.model = None
                self.status["loaded"] = False

    def _save(self):
        if self.model is not None:
            joblib.dump(self.model, self.model_path)
            logger.info("ML model saved to %s", self.model_path)

    def _extract_features_from_readings(self, readings: List[Dict[str, Any]]) -> Dict[str, float]:
        values = {}
        for feature in ["temperature", "humidity", "co2"]:
            match = next((r.get("value") for r in readings if r.get("sensor_type") == feature), None)
            values[feature] = float(match) if match is not None else np.nan
        return values

    def _compute_baseline_stats(self, X: np.ndarray) -> Dict[str, Dict[str, float]]:
        stats = {}
        for idx, feature in enumerate(self.status["features"]):
            col = X[:, idx]
            stats[feature] = {"mean": float(np.mean(col)), "std": float(np.std(col) + 1e-6)}
        return stats

    def _drift_score(self, recent: np.ndarray, baseline: Dict[str, Dict[str, float]]) -> float:
        if recent.size == 0 or not baseline:
            return None
        scores = []
        for idx, feature in enumerate(self.status["features"]):
            col = recent[:, idx]
            mean_recent = np.mean(col)
            mean_base = baseline[feature]["mean"]
            std_base = baseline[feature]["std"]
            scores.append(abs(mean_recent - mean_base) / (std_base + 1e-6))
        return float(max(scores))

    def train_from_db(self, hours: int = 168, train_interval_hours: int = 24) -> Dict[str, Any]:
        """
        Train a model using past actuator commands (hvac_system) and most recent sensor context.
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cmds = list(
            self.db.actuator_commands.find(
                {"actuator_id": "hvac_system", "timestamp": {"$gte": cutoff}}
            ).sort("timestamp", -1)
        )

        samples: List[List[float]] = []
        labels: List[str] = []

        for cmd in cmds:
            ts = cmd.get("timestamp")
            readings_doc = (
                self.db.sensor_readings.find_one({"timestamp": {"$lte": ts}}, sort=[("timestamp", -1)]) or {}
            )
            readings = readings_doc.get("readings", [])
            feats = self._extract_features_from_readings(readings)
            if any(np.isnan(list(feats.values()))):
                continue
            samples.append([feats["temperature"], feats["humidity"], feats["co2"]])
            labels.append(cmd.get("state", "off"))

        # If not enough data, create synthetic baseline
        if len(samples) < 20:
            logger.warning("Insufficient data (%d). Generating synthetic samples.", len(samples))
            temps = np.linspace(10, 40, 40)
            hums = np.linspace(20, 80, 40)
            co2s = np.linspace(400, 2000, 40)
            for t, h, c in zip(temps, hums, co2s):
                state = "cooling" if t > 28 else "heating" if t < 18 else "fan_only" if c > 1200 else "off"
                samples.append([t, h, c])
                labels.append(state)

        # Encode labels
        state_to_idx = {s: i for i, s in enumerate(self.label_map.values())}
        y = np.array([state_to_idx.get(lbl, 0) for lbl in labels])
        X = np.array(samples)

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        model = RandomForestClassifier(n_estimators=80, max_depth=6, random_state=42, class_weight="balanced")
        model.fit(X_train, y_train)
        f1 = None
        try:
            from sklearn.metrics import f1_score

            y_pred = model.predict(X_val)
            f1 = float(f1_score(y_val, y_pred, average="macro"))
        except Exception:
            f1 = None

        self.model = model
        self._save()

        baseline_stats = self._compute_baseline_stats(X)
        version = self.status.get("version", 0) + 1
        next_retrain = datetime.utcnow() + timedelta(hours=train_interval_hours)

        self.status.update(
            {
                "loaded": True,
                "last_trained": datetime.utcnow().isoformat(),
                "samples": int(len(samples)),
                "f1": f1,
                "version": version,
                "training_window_hours": hours,
                "baseline_stats": baseline_stats,
                "next_retrain_at": next_retrain.isoformat(),
            }
        )
        return self.status

    def check_drift(self, hours: int = 24) -> Dict[str, Any]:
        """
        Compute a simple drift score comparing recent window to baseline stats (max z-diff).
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            readings_docs = list(
                self.db.sensor_readings.find({"timestamp": {"$gte": cutoff}}).sort("timestamp", -1).limit(500)
            )
            samples: List[List[float]] = []
            for doc in readings_docs:
                feats = self._extract_features_from_readings(doc.get("readings", []))
                if any(np.isnan(list(feats.values()))):
                    continue
                samples.append([feats["temperature"], feats["humidity"], feats["co2"]])
            if not samples or not self.status.get("baseline_stats"):
                self.status["drift_score"] = None
                self.status["drift_checked_at"] = datetime.utcnow().isoformat()
                return self.status

            X_recent = np.array(samples)
            drift = self._drift_score(X_recent, self.status["baseline_stats"])
            self.status["drift_score"] = drift
            self.status["drift_checked_at"] = datetime.utcnow().isoformat()
            return self.status
        except Exception as exc:
            logger.error("Drift check failed: %s", exc, exc_info=True)
            self.status["drift_score"] = None
            self.status["drift_checked_at"] = datetime.utcnow().isoformat()
            return self.status

    def predict_commands(self, device_id: str, location: str, readings: List[Dict[str, Any]]) -> List[ActuatorCommand]:
        """Predict actuator commands given current readings."""
        feats = self._extract_features_from_readings(readings)
        # Heuristic fallback if model missing or NaNs
        if self.model is None or any(np.isnan(list(feats.values()))):
            return self._heuristic_commands(feats, location)

        X = np.array([[feats["temperature"], feats["humidity"], feats["co2"]]])
        pred_idx = int(self.model.predict(X)[0])
        state = self.label_map.get(pred_idx, "off")
        reason = f"ML v{self.status.get('version', 0)} recommendation"

        return [
            ActuatorCommand(
                actuator_id="hvac_system",
                actuator_type="climate_control",
                state=state,
                reason=reason,
                triggered_by="ml_model",
            )
        ]

    def _heuristic_commands(self, feats: Dict[str, float], location: str) -> List[ActuatorCommand]:
        cmds: List[ActuatorCommand] = []
        t = feats.get("temperature")
        c = feats.get("co2")
        if t is not None:
            if t > 30:
                cmds.append(
                    ActuatorCommand(
                        actuator_id="hvac_system",
                        actuator_type="climate_control",
                        state="cooling",
                        reason="Heuristic: high temperature",
                        triggered_by="ml_fallback",
                    )
                )
            elif t < 17:
                cmds.append(
                    ActuatorCommand(
                        actuator_id="hvac_system",
                        actuator_type="climate_control",
                        state="heating",
                        reason="Heuristic: low temperature",
                        triggered_by="ml_fallback",
                    )
                )
            elif c is not None and c > 1200:
                cmds.append(
                    ActuatorCommand(
                        actuator_id="hvac_system",
                        actuator_type="climate_control",
                        state="fan_only",
                        reason="Heuristic: elevated CO2",
                        triggered_by="ml_fallback",
                    )
                )
        return cmds

    def get_status(self) -> Dict[str, Any]:
        return self.status
