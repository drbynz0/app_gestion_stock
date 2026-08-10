from django.contrib import admin # type: ignore
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # Configuration de la liste
    list_display = ('id', 'name', 'email', 'formatted_phone', 'company_status', 'ice_truncated', 'created_short')
    list_display_links = ('id', 'name')
    list_filter = ('is_company', 'created_at')
    search_fields = ('name', 'email', 'phone_number', 'ice')
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    # Configuration du formulaire
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'email', 'phone_number')
        }),
        ('Informations supplémentaires', {
            'fields': ('address', 'ice', 'is_company'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    # Méthodes d'affichage personnalisées
    def formatted_phone(self, obj):
        return obj.phone_number if len(obj.phone_number) <= 10 else f"{obj.phone_number[:10]}..."
    formatted_phone.short_description = 'Téléphone'

    def ice_truncated(self, obj):
        return obj.ice[:10] + '...' if obj.ice else '-'
    ice_truncated.short_description = 'ICE'

    def company_status(self, obj):
        return "Entreprise" if obj.is_company else "Particulier"
    company_status.short_description = 'Type'

    def created_short(self, obj):
        return obj.created_at.strftime('%d/%m/%Y')
    created_short.short_description = 'Créé le'

    # Optimisation des requêtes
    def get_queryset(self, request):
        return super().get_queryset(request).defer('address')

    # Validation avant sauvegarde
    def save_model(self, request, obj, form, change):
        if obj.is_company and not obj.ice:
            self.message_user(request, "Attention : ICE manquant pour une entreprise", level='warning')
        super().save_model(request, obj, form, change)

    # Actions supplémentaires
    actions = ['mark_as_company']
    
    def mark_as_company(self, request, queryset):
        updated = queryset.update(is_company=True)
        self.message_user(request, f"{updated} clients marqués comme entreprises")
    mark_as_company.short_description = "Marquer comme entreprise"