import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolve backend/data_store directory relative to this file
CURRENT_DIR = Path(__file__).resolve().parent
DATA_STORE_DIR = CURRENT_DIR.parent.parent / "data_store"

# Category normalization lookup for standard rural enterprise codes
CATEGORY_MAP = {
    "DAIRY": "DAIRY",
    "MILK": "DAIRY",
    "GROCERY": "GROCERY",
    "GENERAL STORE": "GROCERY",
    "POULTRY": "POULTRY",
    "TAILOR": "TAILOR",
    "BOUTIQUE": "TAILOR",
    "BAKERY": "BAKERY",
    "SNACKS": "BAKERY",
    "HANDICRAFT": "HANDICRAFT",
    "WEAVING": "HANDICRAFT",
    "SALON": "SALON",
    "BEAUTY": "SALON",
    "ELECTRONICS": "ELECTRONICS",
    "MOBILE": "ELECTRONICS",
    "HARDWARE": "HARDWARE",
    "BUILDING": "HARDWARE",
}


class MarketIntelligenceEngine:
    @classmethod
    def _normalize_category(cls, raw_category: str) -> str:
        """Extracts standard uppercase key from raw category strings."""
        if not raw_category:
            return "GROCERY"
        
        clean_upper = str(raw_category).strip().upper()
        for key, normalized in CATEGORY_MAP.items():
            if key in clean_upper:
                return normalized
        return "GROCERY"

    @classmethod
    def _load_json_data(cls, filename: str) -> dict:
        """Safely loads a reference JSON file from backend/data_store/."""
        filepath = DATA_STORE_DIR / filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[ML DataStore Error] File not found: {filepath}")
            logger.error(f"[ML DataStore Error] File not found: {filepath}")
            return {}
        except Exception as e:
            print(f"[ML DataStore Error] Failed to parse {filepath}: {e}")
            logger.error(f"[ML DataStore Error] Failed to parse {filepath}: {e}")
            return {}

    @classmethod
    def get_district_demand(cls, district: str) -> dict:
        """Extracts regional demand index metrics."""
        demand_data = cls._load_json_data("district_demand_index.json")
        
        district_info = None
        target_dist = str(district or "").strip().lower()
        
        for d_name, d_val in demand_data.items():
            if d_name.lower() == target_dist:
                district_info = d_val
                break
                
        if not district_info:
            district_info = demand_data.get("default", {
                "per_capita_spend_index": 1.0,
                "demand_elasticity": 0.85,
                "seasonal_variance_pct": 10.0,
                "credit_absorption_capacity": "MEDIUM",
                "high_demand_categories": []
            })
            
        return {
            "demand_score": float(district_info.get("demand_score", 70.0)),
            "per_capita_spend_index": float(district_info.get("per_capita_spend_index", 1.0)),
            "seasonal_variance_pct": district_info.get("seasonal_variance_pct", 10.0),
            "absorption_capacity": district_info.get("credit_absorption_capacity", "MEDIUM")
        }

    @classmethod
    def get_sector_economics(cls, category: str) -> dict:
        """Computes wholesale purchase dynamics and tax liabilities."""
        cat_key = cls._normalize_category(category)

        benchmark_data = cls._load_json_data("purchase_price_benchmark.json")
        if not benchmark_data:
            benchmark_data = cls._load_json_data("purchase_price_benchmarks.json")
            
        benchmarks = benchmark_data.get(cat_key, {
            "avg_gross_margin_pct": 25.0,
            "inventory_turnover_days": 20,
            "working_capital_share_pct": 50.0,
            "supplier_credit_days": 15
        })

        tax_data = cls._load_json_data("gst_tax_slabs.json")
        taxes = tax_data.get(cat_key, {
            "gst_rate_pct": 5.0,
            "input_tax_credit_eligible": True,
            "composition_scheme_eligible": True,
        })
        
        return {
            "gross_margin": float(benchmarks.get("avg_gross_margin_pct") or benchmarks.get("gross_margin") or 25.0),
            "gst_rate": float(taxes.get("gst_rate_pct") or taxes.get("gst_rate") or 5.0),
            "inventory_turnover_days": benchmarks.get("inventory_turnover_days", 20),
            "working_capital_share_pct": benchmarks.get("working_capital_share_pct", 50.0)
        }