"""
ai_services.py
AI Engine — Google Gemini via structured JSON output (Pydantic schema).
This is the ONLY file allowed to touch an LLM. It never computes money math;
calculators.py has already produced financial figures before this is called.
"""
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


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
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = f"""
    You are an institutional micro-enterprise advisor for rural India (State Channelizing
    Agencies & NABARD). Generate an uncompromising, data-driven business feasibility study
    tailored for a first-time rural micro-entrepreneur.

    BUSINESS PROFILE:
    - Business Category: {business_category}
    - Location: Village: {geo_data['village']}, Block: {geo_data['block']}, District: {geo_data['district']}
    - Local Competitors within 10km: {geo_data['competitor_count_10km']}
    - Market Saturation Index: {geo_data['saturation_level']}

    FINANCIAL STRUCTURE (DETERMINISTIC — already computed, do not recalculate):
    - Available Margin Capital (10%): Rs.{financial_data['margin_capital']}
    - Total Feasible Project Cost: Rs.{financial_data['total_project_cost']}
    - SCA Loan Eligibility (90%): Rs.{financial_data['loan_amount']}
    - Selected Scheme: {financial_data['scheme_name']} ({financial_data['interest_rate_pa']}% p.a.,
      {financial_data['tenure_years']} years, {financial_data['moratorium_months']} months moratorium)

    RULES:
    1. Ground all recommendations strictly in the socio-economic reality of {geo_data['district']}.
    2. Suggest realistic unit pricing based on rural purchasing power.
    3. Output the entire response in the language specified: {language}.
    4. Never restate or alter the financial figures above — treat them as fixed inputs.
    """

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
