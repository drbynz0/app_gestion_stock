from rest_framework.permissions import BasePermission


class IsCompanyUser(BasePermission):
    """Rejette les requêtes des comptes qui ne sont pas affectés à une entreprise active."""
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and 
            user.is_authenticated and 
            user.company_id and 
            user.company.is_active
        )


class CompanyQuerysetMixin:
    """
    Filtre tenant strict pour toutes les vues DRF.
    Aucune entreprise ne peut voir les données d'une autre entreprise.
    Même un compte superadmin est strictement isolé à son entreprise dans l'application.
    """
    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated or not user.company_id:
            return super().get_queryset().none()
        return super().get_queryset().filter(company=user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
