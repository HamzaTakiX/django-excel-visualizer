from django.db import models
from django.utils import timezone
import os

# Create your models here.

class ExcelFile(models.Model):
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='excel_files/')
    file_size = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    rows_count = models.IntegerField(default=0)
    columns_count = models.IntegerField(default=0)

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the file from storage when model is deleted
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

    def get_file_size_display(self):
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_file_extension(self):
        """Return the file extension."""
        return os.path.splitext(self.file_name)[1][1:].upper()

    class Meta:
        ordering = ['-uploaded_at']
