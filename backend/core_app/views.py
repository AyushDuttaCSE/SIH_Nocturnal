import logging
import requests
from dataclasses import is_dataclass, asdict
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Internal Module Imports
from .calculators import structure_loan as calc_structure_loan, saturation_index
from .ai_services import generate_ai_feasibility_study

logger = logging.getLogger(__name__)

# OSM Tag Mappings for Rural Competitor Queries
OSM_CATEGORY_TAGS = {
    "poultry": '["amenity"~"veterinary|marketplace"]["animal"~"poultry|chicken"]',
    "dairy": '["shop"~"dairy|farm"]["produce"~"milk"]',
    "grocery": '["shop"~"convenience|supermarket|general"]',
    "fertilizer": '["shop"~"agrarian|chemist|farm"]',
    "handicraft": '["shop"~"craft|artisan|gift"]',
    "tailor": '["shop"~"tailor|clothes|boutique"]',
    "bakery": '["shop"~"bakery|pastry"]',
    "salon": '["shop"~"hairdresser|beauty"]',
    "electronics": '["shop"~"electronics|mobile_phone"]',
    "hardware": '["shop"~"hardware|doityourself"]',
    "default": '["shop"]'
}


def serialize_structure(obj):
    """Safely converts dataclasses, Pydantic models, or objects with to_dict() into dicts."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return dict(obj)


# --- 1. Finance: Deterministic Loan Structuring ---
@api_view(['POST', 'GET'])
def structure_loan(request):
    """
    Executes Section 3 deterministic loan structuring via calculators.py.
    Accepts margin_capital via POST payload or GET query params.
    """
    if request.method == 'POST':
        margin = request.data.get('margin_capital', 50000)
    else:
        margin = request.query_params.get('margin_capital', 50000)

    try:
        margin = float(margin)
        structure = calc_structure_loan(margin)
        res_data = serialize_structure(structure)
        res_data["status"] = "success"
        return Response(res_data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Loan calculation error: {e}")
        return Response({
            "status": "error",
            "message": f"Calculation failed: {str(e)}"
        }, status=status.HTTP_400_BAD_REQUEST)


# --- 2. Auth: OTP / Citizen Login ---
@api_view(['POST'])
def otp_login(request):
    """
    Citizen login / prototype user verification issuing SimpleJWT tokens.
    """
    phone_or_user = request.data.get('phone') or request.data.get('username') or 'testuser'
    
    # Auto-register/retrieve prototype user
    user, _ = User.objects.get_or_create(username=str(phone_or_user))
    refresh = RefreshToken.for_user(user)
    
    return Response({
        "status": "authenticated",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "username": user.username,
        }
    }, status=status.HTTP_200_OK)


# --- 3. Geo: Competitor Density & Saturation ---
@api_view(['POST', 'GET'])
def competitors_density(request):
    """
    Queries live Overpass API for POIs within radius around (lat, lng)
    and computes the saturation index from calculators.py.
    """
    params = request.data if request.method == 'POST' else request.query_params
    
    try:
        lat = float(params.get('latitude') or params.get('center_lat') or 23.0673)
        lng = float(params.get('longitude') or params.get('center_lng') or 87.3163)
        radius_km = float(params.get('radius_km', 10.0))
    except (ValueError, TypeError):
        lat, lng, radius_km = 23.0673, 87.3163, 10.0

    category_key = str(params.get('business_type') or params.get('category') or 'grocery').lower()
    radius_meters = int(radius_km * 1000)
    tag = OSM_CATEGORY_TAGS.get(category_key, OSM_CATEGORY_TAGS["default"])
    
    query = f"""
    [out:json][timeout:15];
    (
      node{tag}(around:{radius_meters},{lat},{lng});
      way{tag}(around:{radius_meters},{lat},{lng});
    );
    out center;
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    competitors = []
    try:
        res = requests.post(
            overpass_url, 
            data={'data': query}, 
            headers={'User-Agent': 'GramSetu-GeoService/1.0'}, 
            timeout=10
        )
        if res.status_code == 200:
            elements = res.json().get('elements', [])
            for item in elements:
                item_lat = item.get('lat') or item.get('center', {}).get('lat')
                item_lon = item.get('lon') or item.get('center', {}).get('lon')
                if item_lat and item_lon:
                    name = item.get('tags', {}).get('name', f"Nearby {category_key.capitalize()} Outlet")
                    competitors.append({
                        "id": item['id'],
                        "osm_id": item['id'],
                        "name": name,
                        "lat": item_lat,
                        "lon": item_lon,
                        "lng": item_lon,
                        "category": category_key
                    })
    except Exception as e:
        logger.warning(f"Overpass query failed: {e}. Falling back to empty competitor pool.")

    sat_calc = saturation_index(len(competitors))
    saturation_level = sat_calc if isinstance(sat_calc, str) else sat_calc.get("level", "MODERATE")

    return Response({
        "status": "success",
        "category": category_key,
        "center": {"lat": lat, "lng": lng, "lon": lng},
        "radius_km": radius_km,
        "competitor_count": len(competitors),
        "saturation_level": saturation_level,
        "competitors": competitors
    }, status=status.HTTP_200_OK)


# --- 4. Advisory: AI Business Feasibility ---
@api_view(['POST'])
def generate_feasibility(request):
    """
    Generates structured AI advisory using Mistral AI via ai_services.py.
    Directly serves the frontend App.jsx generateFeasibility() call.
    """
    body = request.data or {}
    
    # Financial payload extraction or derivation
    try:
        margin = float(body.get('margin_capital', 50000))
    except (ValueError, TypeError):
        margin = 50000.0

    fin_structure = serialize_structure(calc_structure_loan(margin))
    
    comp_count = int(body.get('competitor_count') or body.get('competitor_count_10km') or 0)
    sat_level = body.get('saturation_level') or saturation_index(comp_count)
    if isinstance(sat_level, dict):
        sat_level = sat_level.get("level", "MODERATE")

    geo_data = {
        "village": body.get('village') or body.get('village_name') or 'Bishnupur',
        "block": body.get('block') or body.get('block_name') or 'Bishnupur',
        "district": body.get('district') or body.get('district_name') or 'Bankura',
        "latitude": body.get('latitude') or body.get('center_lat') or 23.0708,
        "longitude": body.get('longitude') or body.get('center_lng') or 87.3167,
        "competitor_count_10km": comp_count,
        "competitor_count": comp_count,
        "saturation_level": sat_level
    }
    
    business_category = (
        body.get('business_category') 
        or body.get('category_code') 
        or body.get('category') 
        or 'Agri-Retail'
    )
    language = body.get('language', 'en')

    try:
        report = generate_ai_feasibility_study(
            financial_data=fin_structure,
            geo_data=geo_data,
            business_category=business_category,
            language=language
        )
        return Response({
            "status": "success",
            "report": report,
            "finance": fin_structure,
            "geography": geo_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Advisory generation failed: {e}")
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- 5. Integrated Pipeline: Full Evaluation ---
@api_view(['POST'])
def full_feasibility_evaluation(request):
    """
    Unified pipeline executing calculations, spatial competitor queries, 
    and Mistral AI evaluation in a single round-trip.
    """
    data = request.data or {}
    try:
        margin = float(data.get('margin_capital', 50000))
        lat = float(data.get('latitude') or data.get('center_lat') or 23.0673)
        lng = float(data.get('longitude') or data.get('center_lng') or 87.3163)
    except (ValueError, TypeError):
        margin, lat, lng = 50000.0, 23.0673, 87.3163

    category = str(data.get('category') or data.get('business_type') or 'dairy').lower()
    village = data.get('village') or data.get('village_name') or 'Bishnupur'
    block = data.get('block') or data.get('block_name') or 'Bishnupur'
    district = data.get('district') or data.get('district_name') or 'Bankura'
    language = data.get('language', 'en')

    # 1. Deterministic Financials
    fin_data = serialize_structure(calc_structure_loan(margin))

    # 2. OSM Live Competitors
    radius_km = 10.0
    radius_meters = int(radius_km * 1000)
    tag = OSM_CATEGORY_TAGS.get(category, OSM_CATEGORY_TAGS["default"])
    query = f"""
    [out:json][timeout:15];
    (
      node{tag}(around:{radius_meters},{lat},{lng});
      way{tag}(around:{radius_meters},{lat},{lng});
    );
    out center;
    """
    competitors = []
    try:
        res = requests.post(
            "https://overpass-api.de/api/interpreter", 
            data={'data': query}, 
            headers={'User-Agent': 'GramSetu-Pipeline/1.0'}, 
            timeout=10
        )
        if res.status_code == 200:
            for item in res.json().get('elements', []):
                item_lat = item.get('lat') or item.get('center', {}).get('lat')
                item_lon = item.get('lon') or item.get('center', {}).get('lon')
                if item_lat and item_lon:
                    competitors.append({
                        "id": item['id'],
                        "osm_id": item['id'],
                        "name": item.get('tags', {}).get('name', f"Nearby {category.capitalize()} Entity"),
                        "lat": item_lat,
                        "lon": item_lon,
                        "lng": item_lon,
                        "category": category
                    })
    except Exception as e:
        logger.warning(f"Overpass pipeline query failed: {e}")

    sat_calc = saturation_index(len(competitors))
    saturation_level = sat_calc if isinstance(sat_calc, str) else sat_calc.get("level", "MODERATE")

    # 3. AI Advisory
    geo_data = {
        "village": village,
        "block": block,
        "district": district,
        "latitude": lat,
        "longitude": lng,
        "competitor_count_10km": len(competitors),
        "competitor_count": len(competitors),
        "saturation_level": saturation_level
    }
    
    ai_report = generate_ai_feasibility_study(
        financial_data=fin_data,
        geo_data=geo_data,
        business_category=category,
        language=language
    )

    return Response({
        "status": "success",
        "financials": fin_data,
        "geography": {
            "center": {"lat": lat, "lng": lng, "lon": lng},
            "radius_km": radius_km,
            "competitor_count": len(competitors),
            "saturation_level": saturation_level,
            "competitors": competitors
        },
        "report": ai_report,
        "advisory": ai_report
    }, status=status.HTTP_200_OK)


# --- 6. Catch-All Stub for Any Missing URL Patterns ---
def __getattr__(name):
    @api_view(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    def placeholder_view(request, *args, **kwargs):
        return Response({
            "status": "pending_implementation",
            "endpoint": name,
            "message": f"Endpoint '{name}' is currently being developed."
        })
    return placeholder_view