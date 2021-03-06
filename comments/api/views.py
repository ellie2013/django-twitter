from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from utils.permissions import IsObjectOwner
from comments.models import Comment
from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
    CommentSerializerForUpdate,
)
from utils.decorators import required_params
from inbox.services import NotificationService

from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

# Note: CommentViewSet 继承的是 GenericViewSet 而不是 ModelViewSet
# 如果写成 class CommentViewSet(viewsets.ModelViewSet),
# 可以看到list/retrieve a single object 在没有定义list/retrieve method
# 如果写成 class CommentViewSet(viewsets.GenericViewSet):
# 如果用get /api/comments/ or /api/comments/1/ 会return "HTTP 405 Method Not Allowed""
class CommentViewSet(viewsets.GenericViewSet):
    """
    只实现 list, create, update, destroy 的方法
    不实现 retrieve（查询单个 comment） 的方法，因为没这个需求
    """
    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()
    # this is related to the django_filter backend
    filter_fields = ('tweet_id',)

    # post /api/comments/ -> create
    # Get /api/comments/ -> list
    # get /api/comments/1/ -> retrieve
    # delete /api/comments/1/ -> destroy
    # patch /api/comments/1/ -> partial_update
    # put /api/comments/1/ -> update

    def get_permissions(self):
        # 注意要加用 AllowAny() / IsAuthenticated() 实例化出对象
        # 而不是 AllowAny / IsAuthenticated 这样只是一个类名
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['update', 'destroy']:
            return [IsAuthenticated(), IsObjectOwner()]
        return [AllowAny()]

    # GET /api/comments/?tweet_id=1
    @required_params(params=['tweet_id'])
    @method_decorator(ratelimit(key='user', rate='10/s', method='GET', block=True))
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # this is related to the django_filter backend
        # 下面这句话为了提高效率用prefetch_related, 也可以用select_related('user'), 但是select_related 会有join 不好
        comments = self.filter_queryset(queryset) \
            .prefetch_related('user') \
            .order_by('created_at')
        serializer = CommentSerializer(
            comments,
            context={'request': request},
            many=True,
        )
        return Response(
            {'comments': serializer.data},
            status=status.HTTP_200_OK,
        )

    @method_decorator(ratelimit(key='user', rate='3/s', method='POST', block=True))
    def create(self, request, *args, **kwargs):
        data = {
            'user_id': request.user.id,
            'tweet_id': request.data.get('tweet_id'),
            'content': request.data.get('content'),
        }
        # 注意这里必须要加 'data=' 来指定参数是传给 data 的
        # 因为默认的第一个参数是 instance
        serializer = CommentSerializerForCreate(data=data)
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # save 方法会触发 serializer 里的 create 方法，点进 save 的具体实现里可以看到
        comment = serializer.save()
        NotificationService.send_comment_notification(comment)
        return Response(
            CommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @method_decorator(ratelimit(key='user', rate='3/s', method='POST', block=True))
    def update(self, request, *args, **kwargs):
        # get_object 是 DRF 包装的一个函数，会在找不到的时候 raise 404 error
        # 所以这里无需做额外判断
        comment = self.get_object();
        serializer = CommentSerializerForUpdate(
            instance=comment,
            data=request.data,
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        # save 方法会触发 serializer 里的 update 方法，点进 save 的具体实现里可以看到
        # save 是根据 instance 参数有没有传来决定是触发 create 还是 update
        comment = serializer.save()
        return Response(
            CommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @method_decorator(ratelimit(key='user', rate='5/s', method='POST', block=True))
    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        # DRF 里默认 destroy 返回的是 status code = 204 no content
        # 这里 return 了 success=True 更直观的让前端去做判断，所以 return 200 更合适
        return Response({'success': True}, status=status.HTTP_200_OK)
