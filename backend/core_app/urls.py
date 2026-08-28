from django.urls import path
from . import views

urlpatterns = [
    # Remove any nested 'api/v1/' prefixes inside this file!
    path('finance/structure-loan/', views.structure_loan, name='structure_loan'),
    path('geo/competitors-density/', views.competitors_density, name='competitors_density'),
    path('ai/feasibility-study/', views.generate_feasibility_study, name='feasibility_study'),
]
