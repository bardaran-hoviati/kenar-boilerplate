from django.urls import include, path

from matching import views

urlpatterns = [
    path("getVerifiers/<int:post_token>", views.GetVerifiersView.as_view(), name="get_verifiers"),
    path("verifier/", views.VerifierView.as_view(), name="verifier"),
    path("setVerifiers/<int:post_token>", views.SetVerifiersView.as_view(), name="set_verifiers"),
    path("setVerifier/<int:post_token>/<int:verifier_id>", views.SetVerifierView.as_view(), name="set_verifier"),
    path("setVerifierOauth", views.SetVerifierOauthView.as_view(), name="set_verifier_oauth")
]
