from django.shortcuts import render, get_object_or_404
import logging

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts import models as account_models
from addon.models import Post
from accounts import serializers as account_serializers
from .models import Transaction
from .serializers import TransactionSerializer
from survey.models import Survey
from boilerplate.clients import get_divar_kenar_client

from kenar import (
    CreatePostAddonRequest,
    GetUserAddonsRequest,
    DeleteUserAddonRequest,
    GetPostAddonsRequest,
    DeletePostAddonRequest,
    CreateUserAddonRequest,
    IconName,
    Icon,
    TitleRow,
    SubtitleRow,
    SelectorRow,
    ScoreRow,
    LegendTitleRow,
    GroupInfo,
    EventRow,
    EvaluationRow,
    DescriptionRow,
    Color,
    WideButtonBar,
)


from oauth.schemas import OAuthSession, OAuthSessionType
from boilerplate import settings
from kenar.app import Scope
from kenar.oauth import OauthResourceType
from django.shortcuts import redirect
import os
from kenar import ClientConfig
from kenar import Client

logger = logging.getLogger(__name__)


class GetVerifiersView(APIView):
    def get(self, request, post_token):
        try:
            post = account_models.Post.objects.get(divar_post_id=post_token)
        except account_models.Post.DoesNotExist:
            return Response("error: Post not found", status=status.HTTP_404_NOT_FOUND)
        verifiers = post.selected_verifiers.all()
        serializer = account_serializers.VerifierSerializer(verifiers, many=True)
        return Response(data={"verifiers": serializer.data}, status=status.HTTP_200_OK)

class VerifierView(APIView):
    def get(self, request):
        transaction_list = Transaction.objects.filter(verifier=1)
        serializer = TransactionSerializer(transaction_list, many=True)
        return Response(data={"transaction": serializer.data})
    
    def post(self, request):
        transaction_id = request.data.get('transaction_id')
        transaction = get_object_or_404(Transaction, pk=transaction_id)
        
        # if it is not PENDING (.aka 1)
        if transaction.status != 1: 
            return Response(data={"error": "not valid"}, status=status.HTTP_400_BAD_REQUEST)
        
        approval = request.data.get('approval')
        if approval == 'approved':
            transaction.status = 3
            transaction.verifier.transactions_participated_count += 1
            transaction.save()
            transaction.verifier.save()
        elif approval == 'disapproved':
            transaction.status = 4
            transaction.save()
        else:
            return Response(data={"error": "not valid"}, status=status.HTTP_400_BAD_REQUEST)
        
        buyer_survey = Survey.objects.create(side=1, transaction=transaction, target_verifier=transaction.verifier, rating_user=transaction.buyer)
        seller_survey = Survey.objects.create(side=2, transaction=transaction, target_verifier=transaction.verifier, rating_user=transaction.seller.user)


        return Response(data={"message": "Done"})

        

class SetVerifiersView(APIView):
    def post(self, request, post_token):
        try:
            post = account_models.Post.objects.get(divar_post_id=post_token)
        except account_models.Post.DoesNotExist:
            return Response("error: Post not found", status=status.HTTP_404_NOT_FOUND)
        try:
            selected_verifiers = request.data["selected_verifiers"]
            verifiers = account_models.Verifier.objects.filter(id__in=selected_verifiers)
            for verifier in verifiers:
                post.verifiers.add(verifier)

            post.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"set verification error {e}")
            return Response(status=status.HTTP_400_BAD_REQUEST)

class SetVerifierView(APIView):
    def get(self, request, post_token, verifier_id):
        
        oauth_session = OAuthSession(
            post_token=post_token,
            verifier_id=verifier_id,
        )
        request.session[settings.OAUTH_SESSION_KEY] = oauth_session.model_dump(exclude_none=True)
        
        APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
        APP_BASE_URL = "https://" + APP_HOST
        
        kenar_client = Client(ClientConfig(
            app_slug=os.environ.get("KENAR_APP_SLUG"),
            api_key=os.environ.get("KENAR_API_KEY"),
            oauth_secret=os.environ.get("KENAR_OAUTH_SECRET"),
            oauth_redirect_url=APP_BASE_URL + "/matching/setVerifierOauth",
            )
        )
        
        oauth_scopes = [
            Scope(resource_type=OauthResourceType.USER_PHONE),
        ]

        oauth_url = kenar_client.oauth.get_oauth_redirect(
            scopes=oauth_scopes,
            state=oauth_session.state,
        )

        return redirect(oauth_url)


class SetVerifiersView(APIView):
    def post(self, request, post_token):
        try:
            post = account_models.Post.objects.get(divar_post_id=post_token)
        except account_models.Post.DoesNotExist:
            return Response("error: Post not found", status=status.HTTP_404_NOT_FOUND)
        try:
            selected_verifiers = request.data["selected_verifiers"]
            verifiers = account_models.Verifier.objects.filter(id__in=selected_verifiers)
            for verifier in verifiers:
                post.verifiers.add(verifier)

            post.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"set verification error {e}")
            return Response(status=status.HTTP_400_BAD_REQUEST)

class SetVerifierOauthView(APIView):
    def get(self, request, post_token, verifier_id):
        oauth_session = OAuthSession(**request.session.get(settings.OAUTH_SESSION_KEY))
        logger.info(f"sep{oauth_session.verifier_id}")


def add_addons(access_token, post_token, verifiers):
    addons = []
    kenar_client = get_divar_kenar_client()
    for i in range(min(3, len(verifiers))):
        addons.append(EventRow(
            title=f"{verifiers[i].firstname} {verifiers[i].lastname}",
            subtitle=verifiers[i].rate,
            has_indicator=False,
            label="انتخاب",
            has_divider=True,
            link=f"https://salsa.darkube.app/select-verifier/{post_token}?verifier-id={verifiers[i].pk}",
            padded=True,
            icon=Icon(icon_name=IconName.ADD),
            )
        )
    addons.append(
        WideButtonBar(
            button=WideButtonBar.Button(
                title="گزینه های بیشتر ..." if len(verifiers)>3 else "لیست کامل", link="https://salsa.darkube.app/select-verifier/{post_token}"
            ),
        )
    )

    resp = kenar_client.addon.create_post_addon(
            access_token=access_token,
            data=CreatePostAddonRequest(
                token=post_token,
                widgets=addons,
            ),
        )
    
    logger.info(resp)
