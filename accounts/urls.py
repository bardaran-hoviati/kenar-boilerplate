from django.urls import path
from accounts.views import *

urlpatterns = [
    path('', GetPhoneOauthView.as_view(), name='get-phone-oauth-view'),
]
