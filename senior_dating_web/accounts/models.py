from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField()
    location = models.CharField(max_length=255)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)  # Field for the profile picture
    def __str__(self):
        return self.username

    
class Match(models.Model):
    user1 = models.ForeignKey(User, related_name='matches_as_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='matches_as_user2', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user1} matched with {self.user2}"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"


class Friendship(models.Model):
    from_user = models.ForeignKey(User, related_name='friendships_initiated', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friendships_received', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')  # Prevent duplicate friendships

    def __str__(self):
        return f"{self.from_user} is friends with {self.to_user}"
    


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')  # Ensure a user can only send one request at a time

    def __str__(self):
        return f"Friend request from {self.from_user} to {self.to_user}"
    

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"
    
    