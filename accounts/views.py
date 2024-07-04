from django.shortcuts import render, redirect
from kenar.oauth import OauthResourceType
from rest_framework.views import APIView

from boilerplate import settings
from boilerplate.clients import get_divar_kenar_client
from oauth.schemas import OAuthSession, OAuthSessionType
from kenar.app import Scope, ClientConfig
from kenar import Client


class GetPhoneOauthView(APIView):
    def get(self, request):
        callback_url = request.query_params.get("return_url")
        post_token = request.query_params.get("post_token")
        verifier_id = request.query_params.get("verifier_id", None)

        oauth_session = OAuthSession(
            callback_url=callback_url,
            type=OAuthSessionType.PHONE,
            post_token=post_token,
            verifier_id=verifier_id
        )
        request.session[settings.OAUTH_SESSION_KEY] = oauth_session.model_dump(exclude_none=True)

        # settings_config = settings.ClientConfig
        # config = ClientConfig(app_slug=settings_config.app_slug,
        #                       api_key=settings_config.api_key,
        #                       oauth_secret=settings_config.oauth_secret,
        #                       oauth_redirect_url=)
        # kenar_client = Client(config)\

        kenar_client = get_divar_kenar_client()
        oauth_scopes = [
            Scope(resource_type=OauthResourceType.USER_PHONE),
        ]

        oauth_url = kenar_client.oauth.get_oauth_redirect(
            scopes=oauth_scopes,
            state=oauth_session.state,
        )

        return redirect(oauth_url)
# Create your views here.
