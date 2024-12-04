from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User  # Import your custom User model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.password_validation import  ValidationError as PasswordValidationError


class CustomUserCreationForm(UserCreationForm):
    SECURITY_QUESTIONS = [
        ("What is your mother’s maiden name?", "What is your mother’s maiden name?"),
        ("What was the name of your first pet?", "What was the name of your first pet?"),
        ("What was the name of your elementary school?", "What was the name of your elementary school?"),
    ]

    security_question_1 = forms.ChoiceField(choices=SECURITY_QUESTIONS, label="Security Question 1")
    security_answer_1 = forms.CharField(max_length=255, label="Answer to Security Question 1")
    security_question_2 = forms.ChoiceField(choices=SECURITY_QUESTIONS, label="Security Question 2")
    security_answer_2 = forms.CharField(max_length=255, label="Answer to Security Question 2")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'name', 'age', 'gender', 'location', 'bio', 
                  'security_question_1', 'security_answer_1', 'security_question_2', 'security_answer_2']


class EmailForm(forms.Form):
    email = forms.EmailField(label="Email")


class UpdateBioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['bio']  # Only allow updating the 'bio' field

class MatchFilterForm(forms.Form):
    min_age = forms.IntegerField(required=False, label='Min Age')
    max_age = forms.IntegerField(required=False, label='Max Age')
    gender = forms.ChoiceField(choices=[('', 'Any'), ('M', 'Male'), ('F', 'Female')], required=False, label='Gender')
    location = forms.CharField(max_length=100, required=False, label='Location')


class UpdateProfileImageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_image']


class SecurityQuestionForm(forms.Form):
    username = forms.CharField(max_length=150, label='Username')
    security_answer_1 = forms.CharField(max_length=255, label='Answer to Security Question 1')
    security_answer_2 = forms.CharField(max_length=255, label='Answer to Security Question 2')


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        label='New Password',
        validators=[validate_password]
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirm Password'
    )

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        try:
            validate_password(new_password)
        except PasswordValidationError as e:
            raise forms.ValidationError(e.messages)
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Passwords do not match. Please try again.")
        return cleaned_data