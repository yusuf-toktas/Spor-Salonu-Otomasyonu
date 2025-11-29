from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import MembershipPlan, UserSubscription, Message
from datetime import date, timedelta

User = get_user_model()

class GymPlatformRoleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='member', password='password')
        self.trainer = User.objects.create_user(username='trainer', password='password', is_trainer=True)
        self.other_member = User.objects.create_user(username='other_member', password='password')

    def test_inbox_visibility_member(self):
        self.client.login(username='member', password='password')
        response = self.client.get('/inbox/')
        self.assertEqual(response.status_code, 200)
        users_in_context = response.context['users']

        # Member should see trainer
        self.assertTrue(self.trainer in users_in_context)
        # Member should NOT see other member
        self.assertFalse(self.other_member in users_in_context)

    def test_inbox_visibility_trainer(self):
        self.client.login(username='trainer', password='password')
        response = self.client.get('/inbox/')
        self.assertEqual(response.status_code, 200)
        users_in_context = response.context['users']

        # Trainer should see members
        self.assertTrue(self.user in users_in_context)
        self.assertTrue(self.other_member in users_in_context)
