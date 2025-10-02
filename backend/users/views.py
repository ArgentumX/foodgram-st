# users/views.py
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage

from .serializers import SubscriptionSerializer, UserSerializer
from .models import Subscription, User


class CustomUserViewSet(UserViewSet):

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get']
    )
    def subscriptions(self, request):
        authors = User.objects.filter(subscribers__subscriber=request.user)
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete']
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)
        if request.user == author:
            return Response({'error': 'Self-subscription is not allowed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # POST
        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                subscriber=request.user, author=author
            )
            if not created:
                return Response({'error': 'Already subscribed.'},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = SubscriptionSerializer(
                author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE
        subscription = Subscription.objects.filter(
            subscriber=request.user, author=author
        ).first()
        if not subscription:
            return Response({'error': 'Not subscribed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': ['Обязательное поле.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = UserSerializer(
                user, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            avatar_url = None
            if user.avatar:
                avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

        # DELETE
        if not user.avatar:
            return Response({'detail': 'Avatar not set.'}, status=status.HTTP_400_BAD_REQUEST)
        user.avatar.delete(save=False)
        user.avatar = None
        user.save(update_fields=['avatar'])
        return Response(status=status.HTTP_204_NO_CONTENT)
