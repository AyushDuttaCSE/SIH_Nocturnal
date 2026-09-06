"""
ai_services.py
AI Engine — Direct Mistral AI REST integration via requests.
Zero external SDK dependencies to prevent Python 3.14 namespace issues.
"""
import os
import json
import logging
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


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
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        logger.warning("MISTRAL_API_KEY missing in environment. Engaging fallback.")
        return _build_fallback(financial_data, geo_data, business_category)

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

    system_prompt = (
        "You are an institutional micro-enterprise advisor for rural India (State Channelizing "
        "Agencies & NABARD). Generate an uncompromising, data-driven business feasibility study "
        "tailored for a first-time rural micro-entrepreneur. Output strictly valid JSON."
    )

    user_prompt = f"""
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
    5. Respond ONLY with valid JSON using this exact schema:
    {{
      "market_reach_summary": "string",
      "opportunity_analysis": ["string", "string", "string"],
      "swot_strengths": ["string", "string"],
      "swot_weaknesses": ["string", "string"],
      "swot_opportunities": ["string", "string"],
      "swot_threats": ["string", "string"],
      "localized_risks": ["string", "string"],
      "pricing_strategy": {{"Tier 1": "pricing details", "Tier 2": "pricing details"}},
      "bank_dpr_summary": "string"
    }}
    """

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    # Sequence of models to try in case of rate limits on specific tiers
    candidate_models = ["open-mistral-7b", "mistral-small-latest", "mistral-tiny"]

    for model in candidate_models:
        payload = {
            "model": model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            response = requests.post(MISTRAL_API_URL, headers=headers, json=payload, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                raw_text = data["choices"][0]["message"]["content"]
                return AdvisoryResponseSchema.model_validate_json(raw_text).model_dump()
            
            print(f"[Mistral Alert] Model '{model}' failed with status {response.status_code}: {response.text[:200]}")
            if response.status_code == 429:
                continue  # Try next model in list

        except Exception as e:
            print(f"[Mistral Request Error on {model}]: {e}")
            continue

    logger.warning("All Mistral candidate models exhausted or rate-limited. Engaging deterministic fallback.")
    return _build_fallback(financial_data, geo_data, business_category)


def _build_fallback(financial_data: dict, geo_data: dict, business_category: str) -> dict:
    village = geo_data.get('village', 'Local Village')
    block = geo_data.get('block', 'Local Block')
    margin_cap = financial_data.get('margin_capital', 0)
    project_cost = financial_data.get('total_project_cost', 0)
    loan_amount = financial_data.get('loan_amount', 0)
    scheme_name = financial_data.get('scheme_name', 'Rural Priority Credit')
    moratorium = financial_data.get('moratorium_months', 6)
    comp_count = geo_data.get('competitor_count_10km', geo_data.get('competitor_count', 0))

    return {
        "market_reach_summary": f"Primary target audience within a 5-10km radius of {village}, covering local weekly haats and resident households.",
        "opportunity_analysis": [
            f"Direct retail delivery across {block}",
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