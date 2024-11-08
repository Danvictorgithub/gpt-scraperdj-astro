from django.db import models

# Create your models here.

class Conversation(models.Model):
    start_conversation = models.TextField()
    end_conversation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'conversations'
