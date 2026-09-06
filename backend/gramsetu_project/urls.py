from django.contrib import admin
from django.urls import path, include
from core_app import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Standard API prefix used by frontend/src/api/client.js
    path('api/', include('core_app.urls')),

    # Versioned prefix for backward compatibility
    path('api/v1/', include('core_app.urls')),

    # Direct legacy/explicit pipeline alias
    path('api/analysis/full-evaluation/', views.full_feasibility_evaluation, name='legacy_full_evaluation'),
]