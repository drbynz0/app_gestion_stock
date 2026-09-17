from django.urls import path, include # type: ignore
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import ObtainAuthToken # type: ignore
from rest_framework_simplejwt.views import TokenRefreshView

obtain_auth_token = ObtainAuthToken.as_view() # For the mobile app


from .views import (
    LoginView,
    CompanyRegisterView,
    CompanySettingsView,
    CompanyAdminViewSet,
    SellerListView, # Connection to the login view
    SellerRegisterView, # Créer un compte vendeur
    SellerUpdateView,
    SellerDeleteView,
    ProfileView, # View for the profile
    SellerDashboard, # Connection to the seller dashboard view
)

urlpatterns = [
    path('login-view/', LoginView.as_view(), name='login'),
    path('login-app/', obtain_auth_token, name='login-app'),  # For the mobile app
    path('companies/register/', CompanyRegisterView.as_view(), name='company-register'),
    path('company/settings/', CompanySettingsView.as_view(), name='company-settings'),
    path('sellers/', SellerListView.as_view(), name='seller-list'),
    path('sellers/create/', SellerRegisterView.as_view(), name='register-seller'),
    path('sellers/update/<int:pk>/', SellerUpdateView.as_view(), name='seller-update'),
    path('sellers/delete/<int:pk>/', SellerDeleteView.as_view(), name='seller-delete'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('sellers/details/', SellerDashboard.as_view(), name='seller-dashboard'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

router = DefaultRouter()
router.register(r'platform/companies', CompanyAdminViewSet, basename='platform-company')
urlpatterns += [path('', include(router.urls))]
