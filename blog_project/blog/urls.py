from django.urls import path
from . import views

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('my-posts/', views.my_posts, name='my_posts'),
    path('post/create/', views.post_create, name='post_create'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<slug:slug>/update/', views.post_update, name='post_update'),
    path('post/<slug:slug>/delete/', views.post_delete, name='post_delete'),
    path('user-management/', views.user_management, name='user_management'),
    path('change-user-role/<int:user_id>/', views.change_user_role, name='change_user_role'),
]