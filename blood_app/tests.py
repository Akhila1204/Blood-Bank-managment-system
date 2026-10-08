from django.test import TestCase, Client
from django.contrib.auth.models import User
from blood_app.models import Category, UserProfile, Blood_Donation, Order


class BloodBankBackendTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='O+')
        self.user = User.objects.create_user(
            username='donor_test',
            email='donor@test.com',
            password='Password123!',
            first_name='John',
            last_name='Doe'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            contact='1234567890',
            address='123 Street',
            blood_group=self.category
        )
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='AdminPassword123!'
        )

    def test_public_routes(self):
        routes = ['/', '/about', '/contact', '/gallery', '/login/', '/admin_login', '/signup']
        for url in routes:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Route {url} failed to return 200")

    def test_invalid_login_does_not_crash(self):
        response = self.client.post('/login/', {'uname': 'nonexistent', 'pwd': 'wrong'})
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/admin_login', {'uname': 'nonexistent', 'pwd': 'wrong'})
        self.assertEqual(response.status_code, 200)

    def test_user_authentication_flow(self):
        response = self.client.post('/login/', {'uname': 'donor_test', 'pwd': 'Password123!'})
        self.assertRedirects(response, '/profile')

        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)

    def test_admin_authentication_flow(self):
        response = self.client.post('/admin_login', {'uname': 'admin_test', 'pwd': 'AdminPassword123!'})
        self.assertRedirects(response, '/admin_home')

        response = self.client.get('/admin_home')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_protected_routes_redirect(self):
        user_routes = ['/profile', '/search_blood', '/donate_blood', '/history', '/my_order', '/change_password']
        for url in user_routes:
            response = self.client.get(url)
            self.assertIn(response.status_code, [301, 302])

        admin_routes = ['/admin_home', '/view_user', '/all_order', '/view_category', '/add_category']
        for url in admin_routes:
            response = self.client.get(url)
            self.assertIn(response.status_code, [301, 302])

    def test_models_string_representation(self):
        self.assertEqual(str(self.category), 'O+')
        self.assertEqual(str(self.profile), 'donor_test')

        donation = Blood_Donation.objects.create(
            user=self.profile,
            blood_group=self.category,
            purpose='Blood Donor',
            status='Approved',
            place='City Hospital'
        )
        self.assertIn('donor_test', str(donation))

        order = Order.objects.create(
            user=self.profile,
            blood_donation=donation,
            amount='2000',
            status='Pending'
        )
        self.assertIn('donor_test', str(order))
