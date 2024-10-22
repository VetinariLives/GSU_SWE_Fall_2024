from django.urls import path
from . import views
from django.contrib.auth import views as auth_views





urlpatterns = [
    path('register/', views.register, name='register'),
    path('matches/', views.find_matches, name='find_matches'),
    path('send_message/<int:user_id>/', views.send_message, name='send_message'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('main/', views.main_page, name='main_page'),  # Main page URL
    path('delete_account/', views.delete_account, name='delete_account'),  # Add this URL
    path('update_bio/', views.update_bio, name='update_bio'),
    path('update_profile_image/', views.update_profile_image, name='update_profile_image'),  # Add this URL for updating the profile image
    path('add_friend/<int:user_id>/', views.add_friend, name='add_friend'),  # URL to add a friend
    path('send_friend_request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('accept_friend_request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('decline_friend_request/<int:request_id>/', views.decline_friend_request, name='decline_friend_request'),
    path('send_message/<int:user_id>/', views.send_message, name='send_message'),
    path('remove_friend/<int:user_id>/', views.remove_friend, name='remove_friend'),
    
    # New
    path('confirm-delete/<int:user_id>/', views.confirm_delete, name='confirm_delete'),

]

