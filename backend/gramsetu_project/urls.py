from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('core_app.urls')), # Combines with core_app paths seamlessly
    # path('finance/structure-loan/', views.structure_loan, name='structure_loan'),
]
