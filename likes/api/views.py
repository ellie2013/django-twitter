

from likes.api.serializers import (
    LikeSerializer,
    LikeSerializerForCreate, LikeSerializerForCancel,
)
from likes.models import Like
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from utils.decorators import required_params


class LikeViewSet(viewsets.GenericViewSet):
    queryset = Like.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = LikeSerializerForCreate

    @required_params(request_attr='data', params=['content_type', 'object_id'])
    def create(self, request, *args, **kwargs):
        serializer = LikeSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(
            LikeSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    # 设计取消like的api时候不要用 httpdelete /api/likes/{like_object_id}
    # 因为如果在前端一个用户点击了like，又很快的在点击一下取消like，如果用上述的delete的方式，url需要知道like的object id
    # 这就意味着如果用户取消点赞必须要等到得到了这个点赞的id，这种体验不好 视频 第二十章 like 1_2_3的43：19
    # 所以取消点赞的api是 POST /api/likes/cancle
    @action(methods=['POST'], detail=False)
    @required_params(request_attr='data', params=['content_type', 'object_id'])
    def cancel(self, request, *args, **kwargs):
        serializer = LikeSerializerForCancel(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer.cancel()
        return Response({'success': True}, status=status.HTTP_200_OK)