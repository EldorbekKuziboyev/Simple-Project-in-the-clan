from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=255)
    video_file = models.FileField()
    file_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title
