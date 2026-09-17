from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCompanyAdmin(BasePermission):
    """Business administrator, independent from Django's back-office flag."""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (
            user.user_type == 'PLATFORM_ADMIN' or user.is_superuser or
            (user.company_id and user.user_type == 'ADMIN')
        ))


class IsPlatformAdmin(BasePermission):
    """Reserved for the SaaS operator; never granted to a tenant administrator."""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.user_type == 'PLATFORM_ADMIN' or user.is_superuser))


class HasCompanyPrivilege(BasePermission):
    """Server-side RBAC. UI visibility must never be the only access control."""
    privilege_by_method = {}

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.company_id:
            return bool(user and user.is_authenticated and (user.user_type == 'PLATFORM_ADMIN' or user.is_superuser))
        if request.method in SAFE_METHODS or user.user_type in ('ADMIN', 'PLATFORM_ADMIN') or user.is_superuser:
            return True
        privilege = self.privilege_by_method.get(request.method)
        return bool(privilege and getattr(getattr(user, 'privileges', None), privilege, False))


class HasCustomerPermission(HasCompanyPrivilege):
    privilege_by_method = {'POST': 'add_client', 'PUT': 'edit_client', 'PATCH': 'edit_client', 'DELETE': 'delete_client'}


class HasSupplierPermission(HasCompanyPrivilege):
    privilege_by_method = {'POST': 'add_supplier', 'PUT': 'edit_supplier', 'PATCH': 'edit_supplier', 'DELETE': 'delete_supplier'}


class HasOrderPermission(HasCompanyPrivilege):
    privilege_by_method = {'POST': 'add_order', 'PUT': 'edit_order', 'PATCH': 'edit_order', 'DELETE': 'delete_order'}
