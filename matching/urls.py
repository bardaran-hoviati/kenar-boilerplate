from django.urls import include, path

from matching import views

urlpatterns = [
    path("getVerifiers/<str:post_token>", views.GetVerifiersView.as_view(), name="get_verifiers"),
    path("verifier/", views.VerifierView.as_view(), name="verifier"),
    path("setVerifiers/<str:post_token>", views.SetVerifiersView.as_view(), name="set_verifiers"),
]
