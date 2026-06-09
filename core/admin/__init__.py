from django.contrib import admin
from django.contrib.admin.models import LogEntry
from unfold.admin import ModelAdmin


@admin.register(LogEntry)
class LogEntryAdmin(ModelAdmin):
    """Log de todas as ações feitas no admin — somente leitura."""
    compressed_fields = True
    list_fullwidth = True
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag_display', 'change_message')
    list_filter = ('action_flag', 'content_type', 'user')
    search_fields = ('user__username', 'object_repr', 'change_message')
    date_hierarchy = 'action_time'

    @admin.display(description='Ação')
    def action_flag_display(self, obj):
        return obj.get_action_flag_display()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
