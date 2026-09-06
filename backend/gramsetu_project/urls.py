from django.contrib import admin
from django.urls import path, include
from core_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('core_app.urls')),
    path('api/analysis/full-evaluation/', views.full_feasibility_evaluation),
]