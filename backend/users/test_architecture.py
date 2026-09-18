from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Company, User, VerificationCode

class CompanyArchitectureTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_username_validation(self):
        # Valid username
        company = Company.objects.create(name="Tech Corp", company_username="tech_corp_01")
        user = User(
            username="admin@tech_01",
            email="tech@example.com",
            phone="+2250102030405",
            user_type='ADMIN',
            is_primary_admin=True,
            company=company
        )
        user.set_password("SecurePass123!")
        user.full_clean()
        user.save()
        self.assertEqual(user.username, "admin@tech_01")

        # Invalid username with uppercase
        user_invalid_case = User(
            username="Admin_Invalid",
            email="tech2@example.com",
            company=company
        )
        with self.assertRaises(ValidationError):
            user_invalid_case.full_clean()

        # Invalid username with spaces
        user_invalid_char = User(
            username="admin with space",
            email="tech3@example.com",
            company=company
        )
        with self.assertRaises(ValidationError):
            user_invalid_char.full_clean()

    def test_verification_code_api_flow(self):
        # 1. Send verification code
        resp = self.client.post('/api/security/send-code/', {
            'target': 'verify@example.com',
            'type': 'EMAIL'
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        code = resp.data.get('dev_code') or VerificationCode.objects.filter(target='verify@example.com').latest('id').code
        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)

        # 2. Verify with wrong code
        bad_resp = self.client.post('/api/security/verify-code/', {
            'target': 'verify@example.com',
            'code': '000000',
            'type': 'EMAIL'
        })
        self.assertEqual(bad_resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Verify with correct code
        good_resp = self.client.post('/api/security/verify-code/', {
            'target': 'verify@example.com',
            'code': code,
            'type': 'EMAIL'
        })
        self.assertEqual(good_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(good_resp.data.get('verified'))

    def test_company_deletion_cascade_approach_a(self):
        company = Company.objects.create(name="Delete Me SARL", company_username="deleteme_01")
        primary_admin = User.objects.create_user(
            username="creator_admin",
            email="creator@example.com",
            phone="+2250700000001",
            password="Password123!",
            user_type='ADMIN',
            is_primary_admin=True,
            company=company
        )
        company.created_by = primary_admin
        company.save()

        seller = User.objects.create_user(
            username="seller_user",
            email="seller@example.com",
            phone="+2250700000002",
            password="Password123!",
            user_type='SELLER',
            is_primary_admin=False,
            company=company
        )

        from stock.models import Warehouse, StockLocation
        wh = Warehouse.objects.create(company=company, name="Test Warehouse", code="WH-DEL")
        StockLocation.objects.create(warehouse=wh, name="Zone 1", code="Z1")

        self.assertEqual(User.objects.filter(company=company).count(), 2)

        # Primary admin deletes company with password
        self.client.force_authenticate(user=primary_admin)
        response = self.client.delete('/api/company/settings/', {'password': 'Password123!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify company and all its users are deleted (Approach A)
        self.assertFalse(Company.objects.filter(id=company.id).exists())
        self.assertFalse(User.objects.filter(username="creator_admin").exists())
        self.assertFalse(User.objects.filter(username="seller_user").exists())

    def test_2fa_login_flow(self):
        company = Company.objects.create(name="Secure Co", company_username="secure_co_01")
        user = User.objects.create_user(
            username="secure_admin",
            email="secure@example.com",
            phone="+2250711223344",
            password="SecurePass123!",
            user_type='ADMIN',
            is_primary_admin=True,
            two_factor_enabled=True,
            company=company
        )

        # Login attempt with 2FA enabled
        self.client.logout()
        login_resp = self.client.post('/api/login-app/', {
            'username': 'secure_admin',
            'password': 'SecurePass123!'
        })
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(login_resp.data.get('two_factor_required'))
        code = login_resp.data.get('dev_code')
        user_id = login_resp.data.get('user_id')
        self.assertIsNotNone(code)
        self.assertEqual(user_id, user.id)

        # Submit 2FA code
        verify_resp = self.client.post('/api/security/2fa/verify/', {
            'user_id': user_id,
            'code': code
        })
        self.assertEqual(verify_resp.status_code, status.HTTP_200_OK)
        self.assertIn('token', verify_resp.data)
        self.assertIn('user', verify_resp.data)
        self.assertEqual(verify_resp.data['user']['username'], 'secure_admin')
