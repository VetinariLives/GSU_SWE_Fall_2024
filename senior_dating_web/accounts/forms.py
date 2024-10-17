from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User  # Import your custom User model

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User  # Specify your custom User model
        fields = ['username', 'email', 'password1', 'password2', 'name', 'age', 'gender', 'location', 'bio']  # Include other fields from your User model

class MatchFilterForm(forms.Form):
    min_age = forms.IntegerField(required=False, label='Min Age')
    max_age = forms.IntegerField(required=False, label='Max Age')
    gender = forms.ChoiceField(choices=[('', 'Any'), ('M', 'Male'), ('F', 'Female')], required=False, label='Gender')
    location = forms.CharField(max_length=100, required=False, label='Location')
    

class UpdateProfileImageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_image']