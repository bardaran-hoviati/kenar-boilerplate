import logging

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts import models as account_models
from accounts import serializers as account_serializers
from matching import models as matching_models
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


class SetVerifiersView(APIView):
    def post(self, request, post_token):
        try:
            post = account_models.Post.objects.get(divar_post_id=post_token)
            selected_verifiers = request.data["selected_verifiers"]
            verifiers = account_models.Verifier.objects.filter(id__in=selected_verifiers)
            for verifier in verifiers:
                try:
                    post.verifiers.add(verifier)
                except Exception as e:
                    logger.error(f"Error adding verifier to post in SetVerifiersView: {e}")

            post.save()
            return Response(status=status.HTTP_200_OK)
        except account_models.Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"set verification error {e}")
            return Response(status=status.HTTP_400_BAD_REQUEST)


class SelectVerifierView(APIView):
    def get(self, request, post_token):
        try:
            post = account_models.Post.objects.get(divar_post_id=post_token)
        except account_models.Post.DoesNotExist:
            return Response("error: Post not found", status=status.HTTP_404_NOT_FOUND)
        verifiers = post.selected_verifiers.all()
        serializer = account_serializers.VerifierSerializer(verifiers, many=True)
        return Response(data={"verifiers": serializer.data, "post_token": post_token}, status=status.HTTP_200_OK)

    def post(self, request, post_token):
        try:
            post = account_models.Post.objects.get(divar_post_id=post_token)

            verifier_id = request.data.get("verifier_id", -1)
            user_id = request.data.get("user_id", -1)

            verifier = account_models.Verifier.objects.get(id=verifier_id)
            user = account_models.User.objects.get(id=user_id)
        except account_models.Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        except account_models.Verifier.DoesNotExist:
            return Response({"error": "Verifier not found"}, status=status.HTTP_404_NOT_FOUND)
        except account_models.User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        matching_models.VerificationRequest.objects.create(
            seller=post.seller, verifier=verifier, post=post, claimed_buyer=user, amount=69.5
        )
        return Response({"message": "ok"}, status=status.HTTP_200_OK)


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
            link=f"https://salsa.darkube.app/accounts/?post_token={post_token}&verifier_id={verifiers[i].pk}",
            padded=True,
            icon=Icon(icon_name=IconName.ADD),
        )
        )
    addons.append(
        WideButtonBar(
            button=WideButtonBar.Button(
                title="گزینه های بیشتر ..." if len(verifiers) > 3 else "لیست کامل",
                link=f"https://salsa.darkube.app/accounts/?post_token={post_token}"
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
