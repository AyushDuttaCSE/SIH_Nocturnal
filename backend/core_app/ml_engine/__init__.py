from .viability_classifier import ViabilityClassifier
from .competitor_spatial import CompetitorSpatialAnalyzer
from .market_intelligence import MarketIntelligenceEngine
from .decision_matrix import StrategicDecisionMatrix

def generate_full_ml_evaluation(
    margin_capital: float, 
    category: str, 
    competitor_count: int = 0, 
    district: str = "default", 
    center_lat: float = 23.0, 
    center_lon: float = 87.0, 
    competitors_list: list = None
) -> dict:
    """
    Executes the end-to-end ML intelligence & decision pipeline.
    """
    margin = float(margin_capital)
    
    # 1. Base Financial Structuring
    total_project_cost = margin / 0.10
    loan_amount = total_project_cost * 0.90
    monthly_r = 0.08 / 12.0
    monthly_emi = round((loan_amount * monthly_r * ((1 + monthly_r) ** 60)) / (((1 + monthly_r) ** 60) - 1), 2)

    # 2. Market & Tax Intelligence
    sector_economics = MarketIntelligenceEngine.get_sector_economics(category)
    district_demand = MarketIntelligenceEngine.get_district_demand(district)
    
    # Merge market contexts for the decision matrix
    market_context = {**sector_economics, **district_demand}

    # 3. Spatial Density Analysis
    spatial_data = CompetitorSpatialAnalyzer.extract_spatial_features(
        center_lat=center_lat,
        center_lng=center_lon,
        competitors=competitors_list or [],
        declared_count=competitor_count
    )

    # 4. Viability Inference (Scikit-Learn Classifier)
    feature_payload = {
        "business_category": category,
        "margin_capital": margin,
        "total_project_cost": total_project_cost,
        "monthly_emi": monthly_emi,
        "competitor_count": spatial_data.get("competitor_count", 0),
        "min_distance_km": spatial_data.get("min_distance_km", 5.0),
        "demand_score": district_demand.get("demand_score", 70.0),
        "gross_margin": sector_economics.get("gross_margin", 25.0),
        "gst_rate": sector_economics.get("gst_rate", 5.0)
    }

    ml_output = ViabilityClassifier.predict(feature_payload)

    # 5. Prescriptive Decisions & Strategic Roadmap
    decision = StrategicDecisionMatrix.synthesize_report(
        viability_data=ml_output,
        spatial_data=spatial_data,
        market_context=market_context,
        margin_capital=margin
    )

    return {
        "ml_result": ml_output,
        "features_evaluated": feature_payload,
        "spatial": spatial_data,
        "market": market_context,
        "decision": decision,
        # Alias for backward UI compatibility across advisory cards
        "strategic_recommendations": decision 
    }

__all__ = ["generate_full_ml_evaluation", "ViabilityClassifier"]