from newsfeeds.models import NewsFeed
from friendships.services import FriendshipService


class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
        # 错误的方法
        # 不可以将数据库操作放在 for 循环里面，效率会非常低
        # for follower in FriendshipService.get_followers(tweet.user):
        #     NewsFeed.objects.create(
        #         user=follower,
        #         tweet=tweet,
        #     )

        # 正确的方法：使用 bulk_create，会把 insert 语句合成一条
        newsfeeds = [
            NewsFeed(user=follower, tweet=tweet)
            for follower in FriendshipService.get_followers(tweet.user)
        ]
        # user post a tweet, in the newsfeeds table, it needs to have a record showing user can see the tweet he post
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)