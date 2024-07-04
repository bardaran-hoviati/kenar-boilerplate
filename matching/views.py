from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts import models as account_models
from addon.models import Post
from accounts import serializers as account_serializers
from .models import Transaction
from .serializers import TransactionSerializer
from survey.models import Survey


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

        