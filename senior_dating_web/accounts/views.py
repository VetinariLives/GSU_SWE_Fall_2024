from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from .models import User, Friendship, FriendRequest, Message
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from .forms import MatchFilterForm
from django import forms
from django.db import models
from .forms import UpdateProfileImageForm  # Import the form you created
from django.core.mail import send_mail #New Mail System
from django.contrib import messages  # New 




def home(request):
    if request.user.is_authenticated:
        return redirect('main_page')
    return render(request, 'accounts/home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Save the user and their custom data
            return redirect('home')  # Redirect to home page or login
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def find_matches(request):
    current_user = request.user
    potential_matches = User.objects.exclude(id=current_user.id).filter(gender=current_user.gender)
    return render(request, 'accounts/matches.html', {'matches': potential_matches})

from .models import Message

def send_message(request, user_id):
    receiver = User.objects.get(id=user_id)
    if request.method == 'POST':
        message_text = request.POST['message']
        Message.objects.create(sender=request.user, receiver=receiver, text=message_text)
        return redirect('matches')
    return render(request, 'accounts/send_message.html', {'receiver': receiver})

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Redirect to homepage after login
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def main_page(request):
    user_name = request.user.name  # Access the logged-in user's name
    user_bio = request.user.bio
    profile_image = request.user.profile_image
    return render(request, 'accounts/main_page.html', {'user_name': user_name})

#delete account email confirm
@login_required
def delete_account(request):
    """Render a form to enter email and send confirmation email if correct."""
    if request.method == 'POST':
        entered_email = request.POST.get('email')  # Get the email from the form
        registered_email = request.user.email  # Get the registered email

        if entered_email == registered_email:
            # Send the confirmation email
            send_mail(
                'Confirm Account Deletion',
                f'Hello {request.user.username},\n\n'
                'Click the link below to confirm the deletion of your account:\n'
                f'http://127.0.0.1:8000/accounts/confirm-delete/{request.user.id}/',
                'no-reply@example.com',
                [registered_email],
                fail_silently=False,
            )
            messages.success(request, 'A confirmation email has been sent to your email address.')
            return redirect('main_page')  # Redirect to the main page
        else:
            # Show an error message if the email doesn't match
            messages.error(request, 'The email you entered does not match your account email.')

    # Render the delete account form
    return render(request, 'accounts/delete_account.html')

# accounts/views.py

@login_required
def confirm_delete(request, user_id):
    """Delete the user's account after confirmation."""
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)

    # Log the user out and delete their account
    logout(request)
    user.delete()

    messages.success(request, 'Your account has been successfully deleted.')
    return redirect('home')  # Redirect to the home page







def main_page(request):
    user_name = request.user.name  # Get the logged-in user's name
    user_bio = request.user.bio 
    # Handle filter form
    form = MatchFilterForm(request.GET or None)
    matches = User.objects.exclude(id=request.user.id)  # Get all users except the logged-in user

    if form.is_valid():
        # Filter by age
        min_age = form.cleaned_data.get('min_age')
        max_age = form.cleaned_data.get('max_age')
        gender = form.cleaned_data.get('gender')
        location = form.cleaned_data.get('location')

        if min_age:
            matches = matches.filter(age__gte=min_age)
        if max_age:
            matches = matches.filter(age__lte=max_age)
        if gender:
            matches = matches.filter(gender=gender)
        if location:
            matches = matches.filter(location__icontains=location)

    return render(request, 'accounts/main_page.html', {
        'user_name': user_name,
        'form': form,
        'matches': matches,
        'user_bio': user_bio,
    })

class UpdateBioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['bio']


def update_bio(request):
    if request.method == 'POST':
        form = UpdateBioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()  # Save the updated bio
            return redirect('main_page')  # Redirect to main page after saving
    else:
        form = UpdateBioForm(instance=request.user)

    return render(request, 'accounts/update_bio.html', {'form': form})

def update_profile_image(request):
    if request.method == 'POST':
        form = UpdateProfileImageForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()  # Save the new profile picture
            return redirect('main_page')  # Redirect to the main page after updating
    else:
        form = UpdateProfileImageForm(instance=request.user)

    return render(request, 'accounts/update_profile_image.html', {'form': form})

def add_friend(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    from_user = request.user
    # Check if the friendship already exists
    if not Friendship.objects.filter(from_user=from_user, to_user=to_user).exists():
        Friendship.objects.create(from_user=from_user, to_user=to_user)
    return redirect('main_page')  # Redirect back to the main page

def main_page(request):
    user_name = request.user.name  # Get the logged-in user's name
    user_bio = request.user.bio  # Get the logged-in user's bio
    profile_image = request.user.profile_image  # Get the user's profile picture
    matches = User.objects.exclude(id=request.user.id)  # Get all users except the logged-in user

    # Get friend requests where the current user is the recipient
    incoming_requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
    sent_requests = FriendRequest.objects.filter(from_user=request.user, status='pending')

    # Get the user's friends
    friends = Friendship.objects.filter(from_user=request.user).select_related('to_user')

    return render(request, 'accounts/main_page.html', {
        'user_name': user_name,
        'user_bio': user_bio,
        'profile_image': profile_image,
        'matches': matches,
        'incoming_requests': incoming_requests,
        'sent_requests': sent_requests,
        'friends': friends,  # Pass the friends to the template
    })

def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    from_user = request.user
    # Check if the request already exists or if they're already friends
    if not FriendRequest.objects.filter(from_user=from_user, to_user=to_user).exists():
        FriendRequest.objects.create(from_user=from_user, to_user=to_user)
    return redirect('main_page')

# Accept a friend request
@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.status = 'accepted'
    friend_request.save()
    return redirect('main_page')

# Decline a friend request
@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.delete()  # Remove the friend request
    return redirect('main_page')


def send_message(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            Message.objects.create(sender=request.user, receiver=receiver, text=message_text)
        return redirect('send_message', user_id=receiver.id)
    
    # Fetch the conversation between the two users
    conversation = Message.objects.filter(
        (models.Q(sender=request.user) & models.Q(receiver=receiver)) |
        (models.Q(sender=receiver) & models.Q(receiver=request.user))
    ).order_by('timestamp')

    return render(request, 'accounts/send_message.html', {'receiver': receiver, 'conversation': conversation})

def remove_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    
    # Remove the friendship from both sides (from_user and to_user)
    FriendRequest.objects.filter(from_user=request.user, to_user=friend, status='accepted').delete()
    FriendRequest.objects.filter(from_user=friend, to_user=request.user, status='accepted').delete()
    
    return redirect('main_page')  # Redirect back to the main page