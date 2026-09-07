class StrategicDecisionMatrix:
    @staticmethod
    def synthesize_report(viability_data: dict, spatial_data: dict, market_context: dict, margin_capital: float):
        # --- 1. Top-Level Bank Recommendation ---
        viability = viability_data.get("enterprise_viability", "VIABLE")
        risk = viability_data.get("risk_index", 50.0)
        density = spatial_data.get("density_rating", "MODERATE")
        saturation_level = spatial_data.get("saturation_level", density)

        if viability == "HIGHLY_VIABLE" and saturation_level != "HIGH":
            recommendation = "RECOMMENDED FOR IMMEDIATE SANCTION"
            rationale = "Healthy equity ratio with minimal local competitive overlap."
        elif viability == "HIGH_RISK" or saturation_level == "HIGH" or risk > 60.0:
            recommendation = "CONDITIONAL APPROVAL WITH COLLATERAL BUFFER"
            rationale = "Elevated radial competition and potential market saturation."
        else:
            recommendation = "FEASIBLE UNDER SCA PRIORITY LENDING"
            rationale = "Satisfactory repayment trajectory and standard rural demand metrics."

        # --- 2. Prescriptive Strategic Advisory ---
        actions = []
        warnings = []
        growth_levers = []

        gst_rate = market_context.get("gst_rate", 5.0)
        gross_margin = market_context.get("gross_margin", 25.0)
        comp_count = spatial_data.get("competitor_count", 0)
        min_dist = spatial_data.get("min_distance_km", 5.0)

        # Tax & Regulatory Strategy
        if gst_rate > 0.0:
            actions.append({
                "pillar": "Tax Optimization",
                "title": "Register Under GST Composition Scheme",
                "detail": f"Standard GST is {gst_rate}%. Enrolling in Composition reduces liability to a flat 1%, eliminating complex input tax credit reconciliations."
            })
        else:
            actions.append({
                "pillar": "Tax Optimization",
                "title": "Zero-Tax Agricultural Exemption",
                "detail": "Category is exempt from GST. Maintain local mandi/cooperative purchase receipts to easily access priority sector subvention benefits."
            })

        # Inventory & Cash Flow
        actions.append({
            "pillar": "Procurement & Cash Flow",
            "title": "Strict 15-Day Working Capital Cycle",
            "detail": "Aim to keep working capital lock-in below 50% of operating limits. Secure minimum 15 days credit terms with wholesale distributors to protect cash flow."
        })

        # Spatial Saturation & Competition
        if comp_count >= 5 and min_dist < 1.0:
            warnings.append({
                "title": "High Cluster Proximity Alert",
                "detail": f"{comp_count} direct competitors identified with the nearest only {min_dist}km away. Avoid price undercutting; focus on product bundling and home delivery to peripheral hamlets."
            })
        elif comp_count == 0:
            growth_levers.append({
                "title": "First-Mover Catchment Monopoly",
                "detail": "Zero competitors detected within radial boundary. Secure exclusive distributorships to establish high local switching costs."
            })

        # Margin Expansion
        growth_levers.append({
            "title": "Value Addition & Margin Expansion",
            "detail": f"Local sector average gross margin is {gross_margin}%. Introducing packaged or semi-processed stock can expand net margins by 4-7%."
        })

        return {
            "ml_recommendation": recommendation,
            "rationale": rationale,
            "capital_strength": "ROBUST" if margin_capital >= 50000 else "LEAN",
            "evaluated_risk_index": risk,
            "immediate_actions": actions,
            "risk_warnings": warnings,
            "growth_levers": growth_levers
        }