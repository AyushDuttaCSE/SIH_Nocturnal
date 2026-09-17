import math
import requests
from .models import BankBranch

OSM_CATEGORY_TAGS = {
    "poultry": '["amenity"~"veterinary|marketplace"]["animal"~"poultry|chicken"]',
    "dairy": '["shop"~"dairy|farm"]["produce"~"milk"]',
    "grocery": '["shop"~"convenience|supermarket|general"]',
    "fertilizer": '["shop"~"agrarian|chemist|farm"]',
    "handicraft": '["shop"~"craft|artisan|gift"]',
    "default": '["shop"]'
}


def fetch_live_competitors(lat, lng, business_type, radius_meters=5000):
    tag = OSM_CATEGORY_TAGS.get(business_type.lower(), OSM_CATEGORY_TAGS["default"])
    query = f"""
    [out:json][timeout:15];
    (
      node{tag}(around:{radius_meters},{lat},{lng});
      way{tag}(around:{radius_meters},{lat},{lng});
    );
    out center;
    """
    url = "https://overpass-api.de/api/interpreter"

    try:
        response = requests.post(url, data={'data': query}, headers={'User-Agent': 'GramSetu-Live-App'}, timeout=10)
        if response.status_code == 200:
            data = response.json().get('elements', [])
            competitors = []
            for item in data:
                coords = [item.get('lat') or item.get('center', {}).get('lat'),
                          item.get('lon') or item.get('center', {}).get('lon')]
                if coords[0] and coords[1]:
                    name = item.get('tags', {}).get('name', f"Nearby {business_type.capitalize()} Entity")
                    competitors.append({
                        "id": item['id'],
                        "name": name,
                        "lat": coords[0],
                        "lng": coords[1],
                        "category": business_type
                    })

            density_rating = "Low" if len(competitors) < 3 else "Moderate" if len(competitors) < 8 else "High"
            return {
                "competitor_count": len(competitors),
                "density_rating": density_rating,
                "competitors": competitors
            }
    except Exception as e:
        print(f"Overpass query failed: {e}")

    return {"competitor_count": 0, "density_rating": "Zero Recorded", "competitors": []}


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates distance between two coordinates in kilometers."""
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_banks_for_user(pincode=None, lat=None, lon=None, max_radius_km=15.0):
    """
    Finds banks matching the pincode.
    If user lat/lon is provided, also computes distance and sorts nearest-first.
    """
    results = []

    if pincode:
        clean_pin = str(pincode).strip()
        branches = BankBranch.objects.filter(pincode=clean_pin)

        for branch in branches:
            dist = None
            if lat is not None and lon is not None and branch.latitude and branch.longitude:
                dist = round(haversine_distance(lat, lon, branch.latitude, branch.longitude), 2)

            results.append({
                "id": branch.id,
                "bank_name": branch.bank_name,
                "branch_name": branch.branch_name,
                "address": branch.address,
                "pincode": branch.pincode,
                "latitude": branch.latitude,
                "longitude": branch.longitude,
                "distance_km": dist
            })

    # If user provided lat/lon, sort by proximity
    if lat is not None and lon is not None:
        results.sort(key=lambda x: (x['distance_km'] is None, x['distance_km']))

    return results