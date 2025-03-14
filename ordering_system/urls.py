from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ordering/', include('ordering.urls')),  # Include API routes
]
