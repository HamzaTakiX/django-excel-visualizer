from django import forms
from .models import ExcelFile

class ExcelFileForm(forms.ModelForm):
    class Meta:
        model = ExcelFile
        fields = ['file_name', 'file_size', 'file']
