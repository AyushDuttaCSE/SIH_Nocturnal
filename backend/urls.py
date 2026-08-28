from django.urls import path
from . import views

urlpatterns = [
    path("auth/otp-login/", views.OTPLoginView.as_view(), name="otp-login"),
    path("geo/competitors-density/", views.CompetitorDensityView.as_view(), name="competitors-density"),
    path("finance/structure-loan/", views.StructureLoanView.as_view(), name="structure-loan"),
    path("advisory/generate-feasibility/", views.GenerateFeasibilityView.as_view(), name="generate-feasibility"),
    path("reports/<int:report_id>/download-dpr-pdf/", views.DownloadDPRPdfView.as_view(), name="download-dpr-pdf"),
]
