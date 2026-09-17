from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCompanyUser(BasePermission):
    """Reject accounts that are not assigned to an active tenant."""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (
            user.user_type == 'PLATFORM_ADMIN' or user.is_superuser or
            (user.company_id and user.company.is_active)
        ))


class CompanyQuerysetMixin:
    """Reusable tenant filter for DRF generic views and viewsets."""
    def get_queryset(self):
        if self.request.user.user_type == 'PLATFORM_ADMIN' or self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
