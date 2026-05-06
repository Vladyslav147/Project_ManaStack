from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='category'),
    path('categories/<slug:category_slug>/posts/', views.post_by_category, name='postcategory'),

    # Сначала все четкие пути
    path('my-posts/', views.MyPostView.as_view(), name='my-posts'),
    path('tag/', views.TagListView.as_view(), name='tag'), 
    path('popular/', views.popular_posts, name='popular'),
    path('recent/', views.recent_posts, name='recent'),

    # И только в самом конце — универсальный поиск по слагу
    path('', views.PostListCreateView.as_view(), name='post-list-create'),
    path('<slug:slug>/', views.PostDetailView.as_view(), name='post-detail'),
]