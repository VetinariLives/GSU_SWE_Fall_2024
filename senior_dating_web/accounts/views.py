from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from .models import User, Friendship, FriendRequest, Message
from .forms import CustomUserCreationForm, MatchFilterForm, UpdateProfileImageForm, SecurityQuestionForm, ResetPasswordForm, EmailForm, UpdateBioForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.contrib import messages


# Home page
def home(request):
    if request.user.is_authenticated:
        return redirect('main_page')
    return render(request, 'accounts/home.html')

# Main page view
@login_required
def main_page(request):
    user_name = request.user.name
    user_bio = request.user.bio
    profile_image = request.user.profile_image

    # Fetch matches, friends, etc. (this assumes your models and forms handle these)
    form = MatchFilterForm(request.GET or None)
    matches = User.objects.exclude(id=request.user.id)
    
    # Example logic to fetch friends (assuming you've set up your friendship model)
    friends = FriendRequest.objects.filter(
        (Q(from_user=request.user) | Q(to_user=request.user)),
        status='accepted'
    ).select_related('to_user', 'from_user')

    return render(request, 'accounts/main_page.html', {
        'user_name': user_name,
        'user_bio': user_bio,
        'profile_image': profile_image,
        'form': form,
        'matches': matches,
        'friends': friends,
    })


# Registration
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Save the security questions
            user.security_question_1 = form.cleaned_data['security_question_1']
            user.security_answer_1 = form.cleaned_data['security_answer_1']
            user.security_question_2 = form.cleaned_data['security_question_2']
            user.security_answer_2 = form.cleaned_data['security_answer_2']
            user.save()  # Save the user object to the database
            return redirect('login')  # Redirect to the login page after registration
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def update_bio(request):
    if request.method == 'POST':
        form = UpdateBioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()  # Save the updated bio
            return redirect('main_page')  # Redirect to main page after saving
    else:
        form = UpdateBioForm(instance=request.user)

    return render(request, 'accounts/update_bio.html', {'form': form})

# Finding matches
def find_matches(request):
    current_user = request.user
    matches = User.objects.exclude(id=current_user.id)

    # Exclude friends from matches
    friends = FriendRequest.objects.filter(
        (Q(from_user=current_user) | Q(to_user=current_user)),
        status='accepted'
    ).select_related('to_user', 'from_user')

    friend_ids = [friend.to_user.id if friend.from_user == current_user else friend.from_user.id for friend in friends]
    matches = matches.exclude(id__in=friend_ids)

    # Handle filters
    form = MatchFilterForm(request.GET or None)
    if form.is_valid():
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

    return render(request, 'accounts/matches.html', {'matches': matches, 'form': form})

# Sending messages
def send_message(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            Message.objects.create(sender=request.user, receiver=receiver, text=message_text)
        return redirect('send_message', user_id=receiver.id)

    # Fetch conversation
    conversation = Message.objects.filter(
        (Q(sender=request.user, receiver=receiver) | Q(sender=receiver, receiver=request.user))
    ).order_by('timestamp')

    return render(request, 'accounts/send_message.html', {'receiver': receiver, 'conversation': conversation})

# Forgot Password
def forgot_password(request):
    user = None
    
    if request.method == 'POST' and 'email' not in request.session:
        # Step 1: Email input
        email_form = EmailForm(request.POST)
        if email_form.is_valid():
            email = email_form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                request.session['email'] = email  # Store email in session
                return redirect('forgot_password')  # Redirect to ask security questions
            except User.DoesNotExist:
                email_form.add_error('email', 'No account found with this email.')
    elif request.method == 'POST' and 'email' in request.session:
        # Step 2: Security questions input
        security_form = SecurityQuestionForm(request.POST)
        if security_form.is_valid():
            email = request.session.get('email')
            try:
                user = User.objects.get(email=email)
                answer_1 = security_form.cleaned_data['security_answer_1']
                answer_2 = security_form.cleaned_data['security_answer_2']

                if user.security_answer_1 == answer_1 and user.security_answer_2 == answer_2:
                    request.session['user_id'] = user.id  # Store user ID in session
                    return redirect('reset_password')  # Redirect to reset password page
                else:
                    security_form.add_error(None, 'Security answers do not match.')
            except User.DoesNotExist:
                security_form.add_error(None, 'User not found.')
    else:
        email_form = EmailForm()
        security_form = None

    if 'email' in request.session:
        email = request.session.get('email')
        user = User.objects.get(email=email)
        security_form = SecurityQuestionForm()
        email_form = None

    return render(request, 'accounts/forgot_password.html', {'email_form': email_form, 'security_form': security_form, 'user': user})

# Reset Password
def reset_password(request):
    if 'user_id' not in request.session:
        return redirect('forgot_password')  # Redirect if user hasn't answered security questions

    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)  # Hash the password
            user.save()  # Save the user with the new password
            del request.session['user_id']  # Clear session after resetting password
            return redirect('login')  # Redirect to login page
    else:
        form = ResetPasswordForm()

    return render(request, 'accounts/reset_password.html', {'form': form})


@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    from_user = request.user

    # Check if a friend request already exists or if they are already friends
    if not FriendRequest.objects.filter(from_user=from_user, to_user=to_user).exists() and not FriendRequest.objects.filter(from_user=to_user, to_user=from_user).exists():
        # Create a new friend request
        FriendRequest.objects.create(from_user=from_user, to_user=to_user)
    
    return redirect('main_page')  # Redirect to the main page or wherever appropriate


@login_required
def accept_friend_request(request, request_id):
    # Find the friend request
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)

    # Accept the friend request
    friend_request.status = 'accepted'
    friend_request.save()

    return redirect('main_page')  # Redirect to the main page after accepting the request

def decline_friend_request(request, request_id):
    # Find the friend request based on the request_id and the current logged-in user
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)

    # Decline the friend request by deleting it from the database
    friend_request.delete()

    # Redirect the user back to the main page or wherever appropriate
    return redirect('main_page')


@login_required
def add_friend(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    from_user = request.user

    # Check if a friendship already exists between these users
    if not Friendship.objects.filter(from_user=from_user, to_user=to_user).exists() and not Friendship.objects.filter(from_user=to_user, to_user=from_user).exists():
        # Create a new friendship
        Friendship.objects.create(from_user=from_user, to_user=to_user)
    
    return redirect('main_page')  # Redirect back to the main page or another relevant page

@login_required
def remove_friend(request, user_id):
    # Fetch the friend (the user to be removed) by user_id
    friend = get_object_or_404(User, id=user_id)
    
    # Remove the friendship from both sides (from_user and to_user)
    # This assumes you're using the `FriendRequest` model to represent friendships
    FriendRequest.objects.filter(from_user=request.user, to_user=friend, status='accepted').delete()
    FriendRequest.objects.filter(from_user=friend, to_user=request.user, status='accepted').delete()

    # Redirect back to the main page or any relevant page
    return redirect('main_page')

from django.contrib.auth import get_user_model

@login_required
def confirm_delete(request, user_id):
    """Delete the user's account after confirmation."""
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        # Log the user out and delete their account
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('home')  # Redirect to the home page after deletion

    return render(request, 'accounts/confirm_delete.html', {'user': user})


@login_required
def delete_account(request):
    if request.method == 'POST':
        # Get the email the user entered in the form
        entered_email = request.POST.get('email')
        registered_email = request.user.email  # The registered email in the user account

        if entered_email == registered_email:
            # Delete the user account
            user = request.user
            logout(request)  # Log the user out before deletion
            user.delete()  # Delete the user account
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('home')  # Redirect to the home page after deletion
        else:
            messages.error(request, 'The email you entered does not match your account email.')

    return render(request, 'accounts/delete_account.html')

@login_required
def update_profile_image(request):
    if request.method == 'POST':
        form = UpdateProfileImageForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()  # Save the new profile picture
            return redirect('main_page')  # Redirect to the main page after updating
    else:
        form = UpdateProfileImageForm(instance=request.user)

    return render(request, 'accounts/update_profile_image.html', {'form': form})