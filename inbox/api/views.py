from django_filters.rest_framework import DjangoFilterBackend
from inbox.api.serializers import NotificationSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from notifications.models import Notification

class NotificationViewSet(
    viewsets.GenericViewSet,
    viewsets.mixins.ListModelMixin, # 实现了list的方法。如果不用这个ListModelMixin,需要自己重写这个 def list()
):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fields = ('unread',)

    def get_queryset(self):
        # or return self.request.user.notifications.all()
        return Notification.objects.filter(recipient=self.request.user)

    @action(methods=['GET'], detail=False, url_path='unread-count')
    def unread_count(self, request, *args, **kwargs):
        # GET /api/notifications/unread-count/ url默认的标准是不能有下划线的，所以要用url_path重写一下action name
        # 如果代码比较长，可以这样写
        # Notification.objects.filter(
        #   recipient=self.request.user
        #   unread=True,
        # ).count()
        count = self.get_queryset().filter(unread=True).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='mark-all-as-read')
    def mark_all_as_read(self, request, *args, **kwargs):
        # Notification.objects.update
        updated_count = self.get_queryset().update(unread=False)
        return Response({'marked_count': updated_count}, status=status.HTTP_200_OK)