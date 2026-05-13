from django.urls import path
from . import views

urlpatterns = [
    path('', views.CardListView.as_view(), name='list-card'),
    path('inventory/', views.InventoryCardListCreateView.as_view(), name='inventory'),
    path('inventory/history/', views.InventoryHistoryView.as_view(), name='inventory_history'),
    path('penned_post/', views.PinnedPostView.as_view(), name='penned_post'),
    path('pin_post/', views.pin_post, name='pin_post'),
    path('unpin_post/', views.unpin_post, name='unpin_post'),
    path('get_post_list/', views.get_post_list, name='get_post_list'),
    path('send_mana/', views.send_mana, name='send-mana')
]
