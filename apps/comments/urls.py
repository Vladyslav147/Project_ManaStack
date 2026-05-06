from django.urls import path
from . import views

urlpatterns = [
    path('', views.CommentListCreateView.as_view(), name='comment-list'),
    path('<int:pk>/', views.CommentDetailView.as_view(), name='comment-detail'),
    path('my-comment/', views.MyCommentsView.as_view(), name='my-comments'),
    path('post/<int:post_id>/', views.post_comments, name='post'),
    path('<int:comment_id>/replies/', views.replies_comment, name='replies'),
]
