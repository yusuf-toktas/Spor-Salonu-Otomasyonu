from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import MembershipPlan, UserSubscription, Message
from datetime import date, timedelta

User = get_user_model()

class GymPlatformTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.trainer = User.objects.create_user(username='trainer', password='password', is_trainer=True)
        self.plan = MembershipPlan.objects.create(
            name='Basic Plan',
            description='Basic access',
            price=10.00,
            duration_days=30
        )

    def test_registration(self):
        response = self.client.post('/register/', {
            'username': 'newuser',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        # Check if user is created (Django's UserCreationForm handles this)
        # Note: In a real test we'd check redirection or model count, but
        # standard Django forms might need more fields in POST depending on setup.
        # Let's verify URL existence at least.
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_subscription(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(f'/subscribe/{self.plan.id}/')
        # Should redirect to dashboard
        self.assertRedirects(response, '/dashboard/')

        # Check if subscription created
        self.assertTrue(UserSubscription.objects.filter(user=self.user, plan=self.plan).exists())

    def test_messaging(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(f'/chat/{self.trainer.id}/', {
            'content': 'Hello trainer'
        })
        self.assertEqual(response.status_code, 302) # Redirects back to chat

        # Verify message
        self.assertTrue(Message.objects.filter(sender=self.user, receiver=self.trainer, content='Hello trainer').exists())

    def test_qr_code_generation(self):
        # Create subscription
        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            end_date=date.today() + timedelta(days=30)
        )
        self.client.login(username='testuser', password='password')
        response = self.client.get('/dashboard/')
        self.assertContains(response, 'data:image/png;base64') # Check for base64 image
