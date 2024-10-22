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
    path('delete_account/', views.delete_account, name='delete_account'),  # URL to delete account
    path('update_bio/', views.update_bio, name='update_bio'),  # URL to update bio
    path('update_profile_image/', views.update_profile_image, name='update_profile_image'),  # URL to update profile image
    path('add_friend/<int:user_id>/', views.add_friend, name='add_friend'),  # URL to add a friend
    path('send_friend_request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),  # URL to send friend request
    path('accept_friend_request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),  # URL to accept friend request
    path('decline_friend_request/<int:request_id>/', views.decline_friend_request, name='decline_friend_request'),  # URL to decline friend request
    path('remove_friend/<int:user_id>/', views.remove_friend, name='remove_friend'),  # URL to remove a friend
    
    # Password Reset URLs
    path('forgot_password/', views.forgot_password, name='forgot_password'),  # Forgot Password
    path('reset_password/', views.reset_password, name='reset_password'),  # Reset Password

    # Account Deletion Confirmation
    path('confirm-delete/<int:user_id>/', views.confirm_delete, name='confirm_delete'),  # URL to confirm account deletion
]
