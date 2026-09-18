from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCompanyPrimaryAdmin(BasePermission):
    """
    Administrateur créateur / principal de l'entreprise.
    Seul autorisé à modifier ou supprimer l'entreprise, et à gérer les administrateurs délégués.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.company_id:
            return False
        return bool(user.is_primary_admin or (user.company and user.company.created_by_id == user.id))


class IsCompanyAdmin(BasePermission):
    """
    Administrateur de l'entreprise (qu'il soit créateur principal ou administrateur délégué).
    Accès complet aux modules opérationnels et à l'équipe, mais PAS à la modification/suppression de l'entreprise.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.company_id and user.user_type == 'ADMIN')


class HasCompanyPrivilege(BasePermission):
    """
    Contrôle d'accès RBAC au sein du tenant.
    Un administrateur (principal ou délégué) a tous les accès opérationnels.
    Un vendeur dépend des privilèges assignés.
    """
    privilege_by_method = {}

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.company_id:
            return False
        if request.method in SAFE_METHODS or user.user_type == 'ADMIN':
            return True
        privilege = self.privilege_by_method.get(request.method)
        return bool(privilege and getattr(getattr(user, 'privileges', None), privilege, False))


class HasCustomerPermission(HasCompanyPrivilege):
    privilege_by_method = {'POST': 'add_client', 'PUT': 'edit_client', 'PATCH': 'edit_client', 'DELETE': 'delete_client'}


class HasSupplierPermission(HasCompanyPrivilege):
    privilege_by_method = {'POST': 'add_supplier', 'PUT': 'edit_supplier', 'PATCH': 'edit_supplier', 'DELETE': 'delete_supplier'}


class HasOrderPermission(HasCompanyPrivilege):
    privilege_by_method = {'POST': 'add_order', 'PUT': 'edit_order', 'PATCH': 'edit_order', 'DELETE': 'delete_order'}
