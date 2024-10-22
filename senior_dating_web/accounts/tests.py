from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from .models import User  # Import User for Forgot Password tests
from accounts.models import Message


User = get_user_model()

class EmailVerificationTests(TestCase):
    def setUp(self):
        """Set up a test user with a valid password and initialize the client."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123',
            email='testuser@example.com',
            name='Test User',
            age=30,
            gender='M',
            location='Test City',
            bio='This is a test bio.'
        )
        self.client = Client()

    def test_no_email_sent_for_incorrect_email(self):
        """Test that no email is sent when the email input is incorrect."""
        login = self.client.login(username='testuser', password='testpassword123')
        self.assertTrue(login)
        response = self.client.post(reverse('delete_account'), {
            'email': 'wrongemail@example.com'
        }, follow=True)

        self.assertContains(response, 'The email you entered does not match your account email.')
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_delete_removes_user(self):
        """Test that confirming the deletion removes the user from the database."""
        login = self.client.login(username='testuser', password='testpassword123')
        self.assertTrue(login)
        confirm_url = reverse('confirm_delete', kwargs={'user_id': self.user.id})
        response = self.client.get(confirm_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=self.user.id)


class ForgotPasswordTests(TestCase):

    def setUp(self):
        # Create a test user with security questions
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            age=30,
            security_question_1="What is your mother's maiden name?",
            security_answer_1='Smith',
            security_question_2='What was the name of your first pet?',
            security_answer_2='Buddy'
        )

    def test_forgot_password_starts_with_email_input(self):
        # Ensure the Forgot Password starts with email input
        response = self.client.get(reverse('forgot_password'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email')
        self.assertNotContains(response, 'Security Question')

    def test_security_questions_displayed_after_email(self):
        # Submit the email to proceed to the security questions
        response = self.client.post(reverse('forgot_password'), {'email': 'testuser@example.com'}, follow=True)

        # Ensure the response is successful and contains the security questions
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What is your mother&#x27;s maiden name?")
        self.assertContains(response, "What was the name of your first pet?")

    def test_forgot_password_email_post_redirect(self):
        # Submit the email via POST
        response = self.client.post(reverse('forgot_password'), {'email': 'testuser@example.com'})

        # Ensure it redirects (status code 302)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('forgot_password'))

    def test_security_questions_validation(self):
        # Submit the email to proceed to the security questions
        self.client.post(reverse('forgot_password'), {'email': 'testuser@example.com'})

        # Now, submit the correct security answers
        response = self.client.post(reverse('forgot_password'), {
            'security_answer_1': 'Smith',
            'security_answer_2': 'Buddy'
        }, follow=True)

        # Ensure the user is redirected to the reset password page after correct answers
        self.assertRedirects(response, reverse('reset_password'))

    def test_password_reset(self):
        # Simulate answering the security questions
        self.client.post(reverse('forgot_password'), {'email': 'testuser@example.com'})
        self.client.post(reverse('forgot_password'), {
            'security_answer_1': 'Smith',
            'security_answer_2': 'Buddy'
        })

        # Submit the new password
        response = self.client.post(reverse('reset_password'), {
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })

        # Ensure the password is updated in the database
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))  # Ensure the new password works


class SendMessageTest(TestCase):

    def setUp(self):
        # Create two users: a sender and a receiver, with 'age' field
        self.sender = User.objects.create_user(username='sender', password='testpass123', age=30)
        self.receiver = User.objects.create_user(username='receiver', password='testpass123', age=25)

        # Log in the sender user
        self.client.login(username='sender', password='testpass123')

    def test_send_message(self):
        # The URL for sending a message, using the receiver's user ID
        url = reverse('send_message', kwargs={'user_id': self.receiver.id})

        # Data to send with the POST request (the message content)
        message_data = {
            'message': 'Hello, this is a test message.'
        }

        # Send a POST request to the send_message view
        response = self.client.post(url, data=message_data)

        # Check that the message was created
        self.assertEqual(Message.objects.count(), 1)

        # Get the created message
        message = Message.objects.first()

        # Verify the message content and associations
        self.assertEqual(message.text, 'Hello, this is a test message.')
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)

        # Ensure the view redirects back to the send_message page after sending
        self.assertRedirects(response, reverse('send_message', kwargs={'user_id': self.receiver.id}))
