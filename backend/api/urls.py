"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin # type: ignore
from django.urls import path, include # type: ignore
from django.conf import settings # type: ignore
from django.conf.urls.static import static # type: ignore
from django.views.generic import TemplateView # type: ignore

class ProductsView(TemplateView):
    template_name = "pages/products/products.html"
    
class PromotionsView(TemplateView):
    template_name = "pages/promotions/promotions.html"

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('products/', ProductsView.as_view(), name='products'),
    path('promotions/', PromotionsView.as_view(), name='promotions'),
    path('admin/', admin.site.urls),
    path('api/', include('products.urls')),
    path('api/', include('users.urls')),
    path('api/internal-orders/', include('internalOrders.urls')),
    path('api/external-orders/', include('externalOrders.urls')),
    path('api/', include('customers.urls')),
    path('api/factures/', include('factures.urls')),
    path('api/', include('discounts.urls')),
    path('api/', include('activities.urls')),
    path('api/', include('suppliers.urls')),
    path('api/', include('delivery_notes.urls')),
    path('api/', include('historical.urls')),
    path('api/', include('reset_password.urls')),
    path('api/', include('assistant.urls')),
    path('api/stock/', include('stock.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
