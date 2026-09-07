import numpy as np
from scipy.spatial.distance import pdist

class CompetitorSpatialAnalyzer:
    @staticmethod
    def extract_spatial_features(center_lat: float, center_lng: float, competitors: list, declared_count: int = 0) -> dict:
        """
        Synthesizes advanced spatial density, clustering metrics, and competitive drag factors.
        """
        actual_count = len(competitors) if competitors else declared_count
        
        # 1. Base Density Rating
        if actual_count <= 3:
            density_rating = "UNSATURATED"
            saturation_level = "LOW"
            score_multiplier = 1.15
        elif actual_count <= 12:
            density_rating = "MODERATE"
            saturation_level = "MODERATE"
            score_multiplier = 1.0
        else:
            density_rating = "SATURATED"
            saturation_level = "HIGH"
            score_multiplier = 0.75

        # Early exit if no competitors or missing coords
        if actual_count == 0 or not competitors:
            return {
                "competitor_count": actual_count,
                "min_distance_km": 10.0 if actual_count == 0 else 5.0,
                "avg_distance_km": 10.0 if actual_count == 0 else 5.0,
                "spatial_concentration_index": 0.0 if actual_count == 0 else 0.5,
                "clustering_pattern": "ISOLATED_OPPORTUNITY" if actual_count == 0 else "SPARSE",
                "density_rating": density_rating,
                "saturation_level": saturation_level,
                "competitive_drag_factor": score_multiplier
            }

        # 2. Extract Valid Coordinates
        coords = []
        for c in competitors:
            lat = c.get("lat") or c.get("latitude")
            lng = c.get("lng") or c.get("lon") or c.get("longitude")
            if lat is not None and lng is not None:
                coords.append([float(lat), float(lng)])

        if not coords or center_lat is None or center_lng is None:
            return {
                "competitor_count": actual_count,
                "min_distance_km": 5.0,
                "avg_distance_km": 5.0,
                "spatial_concentration_index": 0.5,
                "clustering_pattern": "SPARSE",
                "density_rating": density_rating,
                "saturation_level": saturation_level,
                "competitive_drag_factor": score_multiplier
            }

        coords_arr = np.array(coords)
        center = np.array([float(center_lat), float(center_lng)])

        # 3. Approximate distances (1 deg lat ~ 111 km, lon ~ 102 km in eastern India)
        lat_diff = (coords_arr[:, 0] - center[0]) * 111.0
        lng_diff = (coords_arr[:, 1] - center[1]) * 102.0
        distances_km = np.sqrt(lat_diff**2 + lng_diff**2)

        min_dist = float(np.min(distances_km))
        avg_dist = float(np.mean(distances_km))

        # 4. Calculate pairwise internal spread
        if len(coords_arr) >= 2:
            pairwise_km = pdist(coords_arr) * 110.0
            concentration_index = float(1.0 / (1.0 + np.mean(pairwise_km)))
        else:
            concentration_index = 0.2

        if min_dist < 1.0:
            pattern = "HIGHLY_CENTRALIZED_BAZAAR"
        elif concentration_index > 0.4:
            pattern = "CLUSTER_FORMATION"
        else:
            pattern = "DECENTRALIZED_SCATTERED"

        return {
            "competitor_count": actual_count,
            "min_distance_km": round(min_dist, 2),
            "avg_distance_km": round(avg_dist, 2),
            "spatial_concentration_index": round(concentration_index, 3),
            "clustering_pattern": pattern,
            "density_rating": density_rating,
            "saturation_level": saturation_level,
            "competitive_drag_factor": score_multiplier
        }