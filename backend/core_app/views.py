import logging
import requests
from django.shortcuts import render
from django.contrib.auth.models import User
from django.conf import settings
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
    "default": '["shop"]'
}


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
        structure = calc_structure_loan(margin)
        res_data = structure.to_dict()
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
    
    lat = float(params.get('latitude', 23.0673))
    lng = float(params.get('longitude', 87.3163))
    radius_km = float(params.get('radius_km', 5.0))
    category = str(params.get('business_type') or params.get('category') or 'grocery').lower()

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
    overpass_url = "https://overpass-api.de/api/interpreter"

    competitors = []
    try:
        res = requests.post(
            overpass_url, 
            data={'data': query}, 
            headers={'User-Agent': 'GramSetu-GeoService'}, 
            timeout=10
        )
        if res.status_code == 200:
            elements = res.json().get('elements', [])
            for item in elements:
                item_lat = item.get('lat') or item.get('center', {}).get('lat')
                item_lon = item.get('lon') or item.get('center', {}).get('lon')
                if item_lat and item_lon:
                    name = item.get('tags', {}).get('name', f"Nearby {category.capitalize()} Store")
                    competitors.append({
                        "id": item['id'],
                        "name": name,
                        "lat": item_lat,
                        "lng": item_lon,
                        "category": category
                    })
    except Exception as e:
        logger.warning(f"Overpass query failed: {e}. Defaulting to empty competitor pool.")

    sat_metrics = saturation_index(len(competitors), radius_km)

    return Response({
        "status": "success",
        "category": category,
        "center": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "competitor_count": len(competitors),
        "saturation_level": sat_metrics["level"],
        "density_per_sq_km": sat_metrics["density_per_sq_km"],
        "competitors": competitors
    }, status=status.HTTP_200_OK)


# --- 4. Advisory: AI Business Feasibility ---
@api_view(['POST'])
def generate_feasibility(request):
    """
    Generates structured AI advisory using Google Gemini via ai_services.py.
    """
    body = request.data
    
    # Financial payload extraction or derivation
    margin = body.get('margin_capital', 50000)
    fin_structure = calc_structure_loan(margin).to_dict()
    
    geo_data = {
        "village": body.get('village', 'Bishnupur'),
        "block": body.get('block', 'Bishnupur'),
        "district": body.get('district', 'Bankura'),
        "competitor_count_10km": body.get('competitor_count', 2),
        "saturation_level": body.get('saturation_level', 'MODERATE')
    }
    
    business_category = body.get('business_category') or body.get('category') or 'Agri-Retail'
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
            "report": report
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
    and Gemini AI evaluation in a single round-trip.
    """
    data = request.data
    margin = data.get('margin_capital', 50000)
    category = str(data.get('category') or data.get('business_type') or 'dairy').lower()
    lat = float(data.get('latitude', 23.0673))
    lng = float(data.get('longitude', 87.3163))
    village = data.get('village', 'Bishnupur')
    block = data.get('block', 'Bishnupur')
    district = data.get('district', 'Bankura')
    language = data.get('language', 'en')

    # 1. Deterministic Financials
    fin_data = calc_structure_loan(margin).to_dict()

    # 2. OSM Live Competitors
    radius_km = 5.0
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
            headers={'User-Agent': 'GramSetu-Pipeline'}, 
            timeout=10
        )
        if res.status_code == 200:
            for item in res.json().get('elements', []):
                item_lat = item.get('lat') or item.get('center', {}).get('lat')
                item_lon = item.get('lon') or item.get('center', {}).get('lon')
                if item_lat and item_lon:
                    competitors.append({
                        "id": item['id'],
                        "name": item.get('tags', {}).get('name', f"Nearby {category.capitalize()} Entity"),
                        "lat": item_lat,
                        "lng": item_lon,
                        "category": category
                    })
    except Exception as e:
        logger.warning(f"Overpass pipeline query failed: {e}")

    sat_metrics = saturation_index(len(competitors), radius_km)

    # 3. AI Advisory
    geo_data = {
        "village": village,
        "block": block,
        "district": district,
        "competitor_count_10km": len(competitors),
        "saturation_level": sat_metrics["level"]
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
            "center": {"lat": lat, "lng": lng},
            "radius_km": radius_km,
            "competitor_count": len(competitors),
            "saturation_level": sat_metrics["level"],
            "density_per_sq_km": sat_metrics["density_per_sq_km"],
            "competitors": competitors
        },
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