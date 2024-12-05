from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from .models import User, Friendship, FriendRequest, Message
from .forms import CustomUserCreationForm, MatchFilterForm, UpdateProfileImageForm, SecurityQuestionForm, ResetPasswordForm, EmailForm, UpdateBioForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.contrib import messages
from .forms import UpdateProfileImageForm
from django.http import HttpResponseForbidden


from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from django.contrib.auth import get_user_model

def home(request):
    if request.user.is_authenticated:
        return redirect('main_page')  # Redirect logged-in users
    return render(request, 'home.html')  # Public homepage


def custom_logout(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('home')


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


# Main page view
@login_required
def main_page(request):

    user_name = request.user.name
    user_bio = request.user.bio
    profile_image = request.user.profile_image

    # Fetch matches, friends, etc.
    form = MatchFilterForm(request.GET or None)
    matches = User.objects.exclude(id=request.user.id)

    # Exclude friends from matches
    friends = FriendRequest.objects.filter(
        (Q(from_user=request.user) | Q(to_user=request.user)),
        status='accepted'
    ).select_related('to_user', 'from_user')

    friend_ids = [friend.to_user.id if friend.from_user == request.user else friend.from_user.id for friend in friends]
    matches = matches.exclude(id__in=friend_ids)

    if form.is_valid():
        # Filter matches based on form data
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

    # Fetch friend requests
    incoming_requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
    sent_requests = FriendRequest.objects.filter(from_user=request.user, status='pending')

    return render(request, 'accounts/main_page.html', {
        'user_name': user_name,
        'user_bio': user_bio,
        'profile_image': profile_image,
        'form': form,
        'matches': matches,
        'friends': friends,
        'incoming_requests': incoming_requests,
        'sent_requests': sent_requests
    })


# Find Matches (Replaced with Code 2 Version)
@login_required
def find_matches(request):
    current_user = request.user
    matches = User.objects.none()  # Default to an empty queryset

    # Handle the filter form
    form = MatchFilterForm(request.GET or None)
    if form.is_valid() and request.GET:  # Check if there are filters applied
        matches = User.objects.exclude(id=current_user.id)

        # Get the friends of the logged-in user and exclude them from the matches
        friends = FriendRequest.objects.filter(
            (Q(from_user=current_user) | Q(to_user=current_user)),
            status='accepted'
        ).select_related('to_user', 'from_user')

        friend_ids = []
        for friend in friends:
            if friend.from_user == current_user:
                friend_ids.append(friend.to_user.id)
            else:
                friend_ids.append(friend.from_user.id)

        matches = matches.exclude(id__in=friend_ids)

        # Apply filters based on form data
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

    return render(request, 'accounts/matches.html', {
        'matches': matches,
        'form': form,
    })



# Sending messages
@login_required
def send_message(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            Message.objects.create(sender=request.user, receiver=receiver, text=message_text)
        return redirect('send_message', user_id=receiver.id)

    conversation = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=receiver)) |
        (Q(sender=receiver) & Q(receiver=request.user))
    ).order_by('timestamp')

    return render(request, 'accounts/send_message.html', {'receiver': receiver, 'conversation': conversation})


# Forgot Password
def forgot_password(request):
    user = None

    if request.method == 'POST' and 'email' not in request.session:
        email_form = EmailForm(request.POST)
        if email_form.is_valid():
            email = email_form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                request.session['email'] = email  # Temporarily store email in session
                return redirect('forgot_password')  # Redirect to ask security questions
            except User.DoesNotExist:
                email_form.add_error('email', 'No account found with this email.')
    elif request.method == 'POST' and 'email' in request.session:
        security_form = SecurityQuestionForm(request.POST)
        if security_form.is_valid():
            email = request.session.get('email')
            try:
                user = User.objects.get(email=email)
                answer_1 = security_form.cleaned_data['security_answer_1']
                answer_2 = security_form.cleaned_data['security_answer_2']

                # Validate security answers
                if user.security_answer_1 == answer_1 and user.security_answer_2 == answer_2:
                    request.session.pop('email', None)  # Remove email from session
                    request.session['user_id'] = user.id  # Store user ID in session temporarily
                    return redirect('reset_password')
                else:
                    security_form.add_error(None, 'Security answers do not match.')
            except User.DoesNotExist:
                security_form.add_error(None, 'User not found.')
    else:
        email_form = EmailForm()
        security_form = None

    if 'email' in request.session:
        email = request.session.get('email')
        try:
            user = User.objects.get(email=email)
            security_form = SecurityQuestionForm()
            email_form = None
        except User.DoesNotExist:
            del request.session['email']  # Clear invalid email from session
            return redirect('forgot_password')  # Redirect to start over

    return render(request, 'accounts/forgot_password.html', {
        'email_form': email_form,
        'security_form': security_form,
        'user': user
    })


# Reset Password

def reset_password(request):
    if 'user_id' not in request.session:
        return redirect('forgot_password')  # Redirect to forgot password if session is missing

    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            del request.session['user_id']  # Clear session after resetting password
            messages.success(request, 'Your password has been reset successfully. You can now log in.')
            return redirect('login')  # Redirect to login page
    else:
        form = ResetPasswordForm()

    return render(request, 'accounts/reset_password.html', {'form': form})


# Updating Bio
@login_required
def update_bio(request):
    if request.method == 'POST':
        form = UpdateBioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('main_page')
    else:
        form = UpdateBioForm(instance=request.user)

    return render(request, 'accounts/update_bio.html', {'form': form})


# Updating Profile Image
@login_required
def update_profile_image(request):
    form = UpdateProfileImageForm(instance=request.user)
    if request.method == 'POST':
        form = UpdateProfileImageForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('main_page')  # Redirect after successful update
    else:
        form = UpdateProfileImageForm(instance=request.user)

    return render(request, 'accounts/update_profile_image.html', {'form': form, 'profile_image': request.user.profile_image})

# Friend Request Handling
@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    from_user = request.user

    if not FriendRequest.objects.filter(from_user=from_user, to_user=to_user).exists() and not FriendRequest.objects.filter(from_user=to_user, to_user=from_user).exists():
        FriendRequest.objects.create(from_user=from_user, to_user=to_user)
    
    return redirect('main_page')


@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.status = 'accepted'
    friend_request.save()
    return redirect('main_page')


@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.delete()
    return redirect('main_page')


@login_required
def remove_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    FriendRequest.objects.filter(from_user=request.user, to_user=friend, status='accepted').delete()
    FriendRequest.objects.filter(from_user=friend, to_user=request.user, status='accepted').delete()
    return redirect('main_page')


# Account Deletion
@login_required
def delete_account(request):
    if request.method == 'POST':
        entered_email = request.POST.get('email')
        registered_email = request.user.email

        if entered_email == registered_email:
            send_mail(
                'Confirm Account Deletion',
                f'Hello {request.user.username},\n\nClick the link below to confirm the deletion of your account:\nhttp://127.0.0.1:8000/accounts/confirm-delete/{request.user.id}/',
                'no-reply@example.com',
                [registered_email],
                fail_silently=False,
            )
            messages.success(request, 'A confirmation email has been sent to your email address.')
            return redirect('main_page')
        else:
            messages.error(request, 'The email you entered does not match your account email.')

    return render(request, 'accounts/delete_account.html')


@login_required
def confirm_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('home')

    return render(request, 'accounts/confirm_delete.html', {'user': user})


@login_required
def add_friend(request, user_id):
    """Adds a friend for the logged-in user."""
    friend = get_object_or_404(User, id=user_id)  # Get the user to be added as a friend
    current_user = request.user

    # Ensure there's no existing friend request or friendship
    existing_request = FriendRequest.objects.filter(from_user=current_user, to_user=friend).exists() or \
                       FriendRequest.objects.filter(from_user=friend, to_user=current_user).exists()
    if existing_request:
        messages.error(request, "Friend request already sent or exists.")
        return redirect('main_page')

    # Create a new friend request
    FriendRequest.objects.create(from_user=current_user, to_user=friend)
    messages.success(request, f"Friend request sent to {friend.username}.")
    return redirect('main_page')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Or use @ensure_csrf_cookie if CSRF middleware is enabled.
def send_confirmation_email(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        # Add logic to send confirmation email here
        return JsonResponse({"message": "Confirmation email sent."}, status=200)
    return JsonResponse({"error": "Invalid request."}, status=400)


def confirm_delete_account(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.user == user:
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('main_page')
    else:
        return HttpResponseForbidden("You are not allowed to perform this action.")