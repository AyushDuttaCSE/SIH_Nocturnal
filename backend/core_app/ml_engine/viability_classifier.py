import os
import joblib
import pandas as pd
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = CURRENT_DIR / "artifacts"

class ViabilityClassifier:
    _pipeline = None

    @classmethod
    def load_pipeline(cls):
        if cls._pipeline is None:
            model_path = ARTIFACTS_DIR / "viability_model.joblib"
            if not model_path.exists():
                from .train_models import train_and_export
                train_and_export()
            cls._pipeline = joblib.load(model_path)
        return cls._pipeline

    @classmethod
    def predict(cls, features: dict):
        pipeline = cls.load_pipeline()

        # Construct DataFrame matching the exact 9 columns defined in train_models.py
        input_df = pd.DataFrame([{
            "business_category": str(features.get("business_category", "GROCERY")).upper(),
            "margin_capital": float(features.get("margin_capital", 50000.0)),
            "total_project_cost": float(features.get("total_project_cost", 500000.0)),
            "monthly_emi": float(features.get("monthly_emi", 9124.0)),
            "competitor_count": int(features.get("competitor_count", 0)),
            "min_distance_km": float(features.get("min_distance_km", 5.0)),
            "demand_score": float(features.get("demand_score", 70.0)),
            "gross_margin": float(features.get("gross_margin", 25.0)),
            "gst_rate": float(features.get("gst_rate", 5.0))
        }])

        pred_class = str(pipeline.predict(input_df)[0])
        probabilities = pipeline.predict_proba(input_df)[0]
        classes = pipeline.classes_.tolist()
        
        prob_dict = {
            cls_name: round(float(prob) * 100, 1) 
            for cls_name, prob in zip(classes, probabilities)
        }

        confidence = round(float(max(probabilities)) * 100, 1)
        
        # Risk index scaling (0 - 100) based on HIGHLY_VIABLE probability and local competition density
        risk_index = round((1.0 - (prob_dict.get("HIGHLY_VIABLE", 0.0) / 100.0)) * 75 + (features.get("competitor_count", 0) * 0.6), 1)
        risk_index = max(5.0, min(95.0, risk_index))

        return {
            "enterprise_viability": pred_class,
            "viability_score": confidence,
            "risk_index": risk_index,
            "class_distribution": prob_dict,
        }