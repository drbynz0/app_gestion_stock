from django.db import models
import random
from django.conf import settings

class PasswordResetCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    @classmethod
    def generate_code(cls, user):
        code = str(random.randint(1000, 9999))
        cls.objects.create(user=user, code=code)
        return code