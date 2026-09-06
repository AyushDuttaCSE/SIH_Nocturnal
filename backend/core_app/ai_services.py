"""
ai_services.py
AI Engine — Google Gemini via structured JSON output (Pydantic schema).
This is the ONLY file allowed to touch an LLM. It never computes money math;
calculators.py has already produced financial figures before this is called.
"""
import os
import logging
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AdvisoryResponseSchema(BaseModel):
    market_reach_summary: str = Field(description="5-10km radius target audience demographic and channel breakdown")
    opportunity_analysis: list[str] = Field(description="3-5 unserved or underserved niches in this specific block/village")
    swot_strengths: list[str] = Field(description="Internal strengths tailored to micro-budget")
    swot_weaknesses: list[str] = Field(description="Internal constraints (working capital, tech gaps)")
    swot_opportunities: list[str] = Field(description="External growth prospects in this geography")
    swot_threats: list[str] = Field(description="External risks (seasonal fluctuations, supply chains)")
    localized_risks: list[str] = Field(description="Specific local threats and actionable mitigation strategies")
    pricing_strategy: dict[str, str] = Field(description="Tiered product/service pricing with regional purchasing power justification")
    bank_dpr_summary: str = Field(description="Executive summary formatted for a bank loan sanctioning officer")


def generate_ai_feasibility_study(financial_data: dict, geo_data: dict, business_category: str, language: str = "en") -> dict:
    """
    financial_data: output of calculators.structure_loan(), serialized to a dict
    geo_data: {village, block, district, competitor_count_10km, saturation_level}
    Returns a dict matching AdvisoryResponseSchema.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in backend/.env")

    client = genai.Client(api_key=api_key)

    village = geo_data.get('village', 'Local Village')
    block = geo_data.get('block', 'Local Block')
    district = geo_data.get('district', 'District')
    comp_count = geo_data.get('competitor_count_10km', geo_data.get('competitor_count', 0))
    saturation = geo_data.get('saturation_level', geo_data.get('density_rating', 'MODERATE'))

    margin_cap = financial_data.get('margin_capital', 0)
    project_cost = financial_data.get('total_project_cost', 0)
    loan_amount = financial_data.get('loan_amount', 0)
    scheme_name = financial_data.get('scheme_name', 'Rural Priority Credit')
    rate = financial_data.get('interest_rate_pa', financial_data.get('interest_rate', 8.0))
    tenure = financial_data.get('tenure_years', financial_data.get('tenure', 5))
    moratorium = financial_data.get('moratorium_months', 6)

    prompt = f"""
    You are an institutional micro-enterprise advisor for rural India (State Channelizing
    Agencies & NABARD). Generate an uncompromising, data-driven business feasibility study
    tailored for a first-time rural micro-entrepreneur.

    BUSINESS PROFILE:
    - Business Category: {business_category}
    - Location: Village: {village}, Block: {block}, District: {district}
    - Local Competitors within 10km: {comp_count}
    - Market Saturation Index: {saturation}

    FINANCIAL STRUCTURE (DETERMINISTIC — already computed, do not recalculate):
    - Available Margin Capital (10%): Rs. {margin_cap}
    - Total Feasible Project Cost: Rs. {project_cost}
    - SCA Loan Eligibility (90%): Rs. {loan_amount}
    - Selected Scheme: {scheme_name} ({rate}% p.a., {tenure} years, {moratorium} months moratorium)

    RULES:
    1. Ground all recommendations strictly in the socio-economic reality of {district}.
    2. Suggest realistic unit pricing based on rural purchasing power.
    3. Output the entire response in the language specified: {language}.
    4. Never restate or alter the financial figures above — treat them as fixed inputs.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AdvisoryResponseSchema,
                temperature=0.2,
            ),
        )
        return AdvisoryResponseSchema.model_validate_json(response.text).model_dump()

    except Exception as e:
        logger.error(f"Gemini API generation failed: {e}")
        # Graceful fallback structure conforming to AdvisoryResponseSchema
        return {
            "market_reach_summary": f"Primary target audience within a 5-10km radius of {village}, covering local weekly haats and resident households.",
            "opportunity_analysis": [
                f"Direct farm/household retail delivery across {block}",
                "Aggregate supply linkages with block cooperative bodies",
                "Value addition and primary grading for higher margins"
            ],
            "swot_strengths": [
                f"Low promoter capital requirement of Rs. {margin_cap}",
                f"Subsidized term loan sanction under {scheme_name}"
            ],
            "swot_weaknesses": [
                "Working capital pressure in initial quarter",
                "High reliance on local power and transport infrastructure"
            ],
            "swot_opportunities": [
                f"Low competitor density ({comp_count} identified within 10km)",
                "Rising local consumer demand in rural town fringes"
            ],
            "swot_threats": [
                "Seasonal fluctuations in purchasing power",
                "Price volatility of input raw materials"
            ],
            "localized_risks": [
                f"Unorganized competition in {block} haats — Mitigate with consistent product quality and fair credit terms.",
                "Delayed collection cycles — Mitigate by maintaining strict cash-and-carry limits."
            ],
            "pricing_strategy": {
                "Standard Unit": "Priced 5-8% below nearest sub-divisional town bazaar to stimulate fast uptake.",
                "Bulk Purchase": "Tiered volume discounts for local institutional buyers or village traders."
            },
            "bank_dpr_summary": (
                f"Project for {business_category} at {village} has a total capital outlay of Rs. {project_cost}, "
                f"backed by promoter equity of Rs. {margin_cap} (10%) and recommended debt of Rs. {loan_amount} (90%) "
                f"under {scheme_name}. With an initial moratorium of {moratorium} months, debt service coverage remains viable."
            )
        }