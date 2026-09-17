from rest_framework.permissions import BasePermission, SAFE_METHODS


class HasProductPermission(BasePermission):
    """Backend RBAC for the catalogue; UI visibility is not a security layer."""
    privilege_by_method = {
        'POST': 'add_product',
        'PUT': 'edit_product',
        'PATCH': 'edit_product',
        'DELETE': 'delete_product',
    }

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.company_id:
            return False
        if request.method in SAFE_METHODS or user.user_type in ('ADMIN', 'PLATFORM_ADMIN') or user.is_superuser:
            return True
        privileges = getattr(user, 'privileges', None)
        return bool(privileges and getattr(privileges, self.privilege_by_method[request.method], False))


class HasCategoryPermission(HasProductPermission):
    privilege_by_method = {
        'POST': 'add_category',
        'PUT': 'edit_category',
        'PATCH': 'edit_category',
        'DELETE': 'delete_category',
    }
