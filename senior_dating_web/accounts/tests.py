from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model

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



   