from django.shortcuts import render
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from google import genai

# --- 1. Finance: Loan Structuring ---
@api_view(['POST', 'GET'])
def structure_loan(request):
    margin_capital = request.data.get('margin_capital', 50000)
    try:
        margin_capital = float(margin_capital)
    except (ValueError, TypeError):
        margin_capital = 50000.0

    # Prototype financial model: 75% loan assistance, 25% promoter contribution
    total_project_cost = margin_capital * 4.0
    loan_amount = total_project_cost * 0.75
    interest_rate_percent = 8.5
    tenure_months = 60

    monthly_rate = (interest_rate_percent / 100) / 12
    emi = (loan_amount * monthly_rate * ((1 + monthly_rate) ** tenure_months)) / (((1 + monthly_rate) ** tenure_months) - 1)

    return Response({
        "status": "success",
        "margin_capital": margin_capital,
        "total_project_cost": round(total_project_cost, 2),
        "eligible_loan_amount": round(loan_amount, 2),
        "tenure_months": tenure_months,
        "annual_interest_rate": f"{interest_rate_percent}%",
        "estimated_monthly_emi": round(emi, 2),
        "subsidy_eligible": True
    })

# --- 2. Auth: OTP / Citizen Login ---
@api_view(['POST'])
def otp_login(request):
    phone_or_user = request.data.get('phone') or request.data.get('username') or 'testuser'
    
    # Fetch or auto-register prototype user
    user, _ = User.objects.get_or_create(username=phone_or_user)
    
    # Issue SimpleJWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        "status": "authenticated",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "username": user.username,
        }
    })

# --- 3. Advisory: AI Business Feasibility ---
@api_view(['POST'])
def generate_feasibility(request):
    prompt = request.data.get('prompt') or request.data.get('query') or 'Assess rural business feasibility.'
    
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key or api_key == 'dummy_key_for_now':
        return Response({
            "status": "demo",
            "report": "Demo Mode: Set a valid GEMINI_API_KEY in your .env file to generate live AI feasibility insights."
        })

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return Response({
            "status": "success",
            "report": response.text
        })
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)

# --- 4. Catch-All Stub for Any Remaining Endpoints ---
def __getattr__(name):
    """
    Dynamically catches remaining endpoints in urls.py (such as competitors_density)
    so routing never throws an AttributeError while endpoints are completed.
    """
    @api_view(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    def placeholder_view(request, *args, **kwargs):
        return Response({
            "status": "pending_implementation",
            "endpoint": name,
            "message": f"Endpoint '{name}' is currently being developed."
        })
    return placeholder_view