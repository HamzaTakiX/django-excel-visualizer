from django.apps import AppConfig

class ExcelAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Excel_App'
    
    def ready(self):
        # Import the template tags when the app is ready
        import Excel_App.templatetags.excel_filters
