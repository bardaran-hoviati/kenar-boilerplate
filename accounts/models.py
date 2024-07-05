from django.db import models
from oauth import models as oauth_models


class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(TimestampModel):
    username = models.CharField(max_length=50, null=True)
    divar_user_phone = models.CharField(max_length=12, null=True, blank=True, unique=True)
    oauth = models.ForeignKey(to=oauth_models.OAuth, on_delete=models.SET_NULL, null=True, blank=True)


class Seller(TimestampModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rate = models.DecimalField(default=0, max_digits=5, decimal_places=3)


class Verifier(TimestampModel):
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    rate = models.DecimalField(decimal_places=2, default=5.0, max_digits=12)
    transactions_participated_count = models.IntegerField(default=0)
    profile_photo = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f'Verifier: {self.firstname} {self.lastname}'


class Post(TimestampModel):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    divar_post_id = models.CharField(max_length=50, unique=True)
    selected_verifiers = models.ManyToManyField(Verifier, null=True, blank=True)

    def __str__(self):
        return f'Post: {self.divar_post_id} by {self.seller.user.username}'

