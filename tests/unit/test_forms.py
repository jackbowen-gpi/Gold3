"""
Comprehensive form tests for GOLD3 project.

Tests Django forms including model forms, form validation, and form handling.
Covers form rendering, submission, validation errors, and edge cases.

Usage:
    python -m pytest tests/unit/test_forms.py -v
    python -m pytest tests/unit/test_forms.py -m unit
"""

import pytest
from django.test import TestCase
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from gchub_db.apps.workflow.models import Site


class TestUserForms(TestCase):
    """Test user-related forms."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="form_test_user",
            email="form_test@example.com",
            password="testpass123",
        )

    @pytest.mark.unit
    def test_user_creation_form(self):
        """Test user creation form validation."""
        from django.contrib.auth.forms import UserCreationForm

        # Valid form data
        form_data = {
            "username": "newuser",
            "password1": "testpass123",
            "password2": "testpass123",
            "email": "newuser@example.com",
        }

        form = UserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Create user
        user = form.save()
        self.assertEqual(user.username, "newuser")
        self.assertTrue(user.check_password("testpass123"))

    @pytest.mark.unit
    def test_user_creation_form_validation_errors(self):
        """Test user creation form validation errors."""
        from django.contrib.auth.forms import UserCreationForm

        # Password mismatch
        form_data = {
            "username": "newuser",
            "password1": "testpass123",
            "password2": "differentpass",
            "email": "newuser@example.com",
        }

        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

        # Duplicate username
        form_data = {
            "username": "form_test_user",  # Already exists
            "password1": "testpass123",
            "password2": "testpass123",
            "email": "another@example.com",
        }

        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    @pytest.mark.unit
    def test_password_change_form(self):
        """Test password change form."""
        from django.contrib.auth.forms import PasswordChangeForm

        # Valid password change
        form_data = {
            "old_password": "testpass123",
            "new_password1": "newpass123",
            "new_password2": "newpass123",
        }

        form = PasswordChangeForm(user=self.user, data=form_data)
        self.assertTrue(form.is_valid())

        # Change password
        form.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))

    @pytest.mark.unit
    def test_password_change_form_errors(self):
        """Test password change form validation errors."""
        from django.contrib.auth.forms import PasswordChangeForm

        # Wrong old password
        form_data = {
            "old_password": "wrongpass",
            "new_password1": "newpass123",
            "new_password2": "newpass123",
        }

        form = PasswordChangeForm(user=self.user, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("old_password", form.errors)

        # Password mismatch
        form_data = {
            "old_password": "testpass123",
            "new_password1": "newpass123",
            "new_password2": "differentpass",
        }

        form = PasswordChangeForm(user=self.user, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("new_password2", form.errors)


class TestModelForms(TestCase):
    """Test Django model forms."""

    def setUp(self):
        """Set up test data."""
        self.site = Site.objects.create(domain="formtest.example.com", name="Form Test Site")
        self.user = User.objects.create_user(username="formuser", email="form@example.com", password="testpass123")

    @pytest.mark.unit
    def test_site_model_form(self):
        """Test Site model form."""
        from django.forms import ModelForm

        class SiteForm(ModelForm):
            class Meta:
                model = Site
                fields = ["domain", "name"]

        # Valid form data
        form_data = {
            "domain": "newsite.example.com",
            "name": "New Test Site",
        }

        form = SiteForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Save form
        site = form.save()
        self.assertEqual(site.domain, "newsite.example.com")
        self.assertEqual(site.name, "New Test Site")

    @pytest.mark.unit
    def test_site_model_form_validation(self):
        """Test Site model form validation."""
        from django.forms import ModelForm

        class SiteForm(ModelForm):
            class Meta:
                model = Site
                fields = ["domain", "name"]

        # Missing required field
        form_data = {
            "domain": "incomplete.example.com",
            # Missing name
        }

        form = SiteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    @pytest.mark.unit
    def test_user_model_form(self):
        """Test User model form."""
        from django.contrib.auth.forms import UserChangeForm

        # Valid form data - include all required fields for UserChangeForm
        form_data = {
            "username": "formtestuser",
            "email": "formtest@example.com",
            "first_name": "Form",
            "last_name": "Test",
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "date_joined": self.user.date_joined.isoformat(),
            "last_login": (self.user.last_login.isoformat() if self.user.last_login else ""),
        }

        form = UserChangeForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

        # Save form
        form.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "formtestuser")


class TestCustomForms(TestCase):
    """Test custom form classes."""

    @pytest.mark.unit
    def test_custom_form_with_validation(self):
        """Test custom form with custom validation."""

        class ContactForm(forms.Form):
            name = forms.CharField(max_length=100, required=True)
            email = forms.EmailField(required=True)
            message = forms.CharField(widget=forms.Textarea, required=True)

            def clean_name(self):
                name = self.cleaned_data["name"]
                if len(name) < 2:
                    raise ValidationError("Name must be at least 2 characters long")
                return name

            def clean(self):
                cleaned_data = super().clean()
                name = cleaned_data.get("name")
                message = cleaned_data.get("message")

                if name and message and name.lower() in message.lower():
                    raise ValidationError("Message cannot contain the name")

                return cleaned_data

        # Valid form
        form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "message": "This is a test message",
        }

        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Invalid name (too short)
        form_data["name"] = "A"
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

        # Invalid message (contains name)
        form_data["name"] = "John Doe"
        form_data["message"] = "John Doe is testing this form"
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    @pytest.mark.unit
    def test_form_with_choices(self):
        """Test form with choice fields."""

        class SurveyForm(forms.Form):
            RATING_CHOICES = [
                ("1", "Poor"),
                ("2", "Fair"),
                ("3", "Good"),
                ("4", "Very Good"),
                ("5", "Excellent"),
            ]

            rating = forms.ChoiceField(choices=RATING_CHOICES, required=True)
            comments = forms.CharField(widget=forms.Textarea, required=False)

        # Valid form
        form_data = {
            "rating": "4",
            "comments": "Great service!",
        }

        form = SurveyForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["rating"], "4")

        # Invalid choice
        form_data["rating"] = "6"  # Not in choices
        form = SurveyForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("rating", form.errors)


class TestFormWidgets(TestCase):
    """Test form widgets and rendering."""

    @pytest.mark.unit
    def test_form_widget_rendering(self):
        """Test form widget rendering."""

        class TestForm(forms.Form):
            text_field = forms.CharField()
            email_field = forms.EmailField()
            date_field = forms.DateField()
            boolean_field = forms.BooleanField()
            choice_field = forms.ChoiceField(choices=[("a", "A"), ("b", "B")])

        form = TestForm()
        html = form.as_p()

        # Check that widgets are rendered
        self.assertIn("text_field", html)
        self.assertIn("email_field", html)
        self.assertIn("date_field", html)
        self.assertIn("boolean_field", html)
        self.assertIn("choice_field", html)

    @pytest.mark.unit
    def test_form_field_attributes(self):
        """Test form field attributes."""

        class TestForm(forms.Form):
            username = forms.CharField(
                max_length=30,
                widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}),
            )
            password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

        form = TestForm()
        username_html = str(form["username"])
        password_html = str(form["password"])

        # Check attributes are applied
        self.assertIn('class="form-control"', username_html)
        self.assertIn('placeholder="Username"', username_html)
        self.assertIn('type="password"', password_html)
        self.assertIn('class="form-control"', password_html)


class TestFormSecurity(TestCase):
    """Test form security features."""

    @pytest.mark.unit
    def test_csrf_protection(self):
        """Test CSRF protection in forms."""
        from django.middleware.csrf import get_token

        # This would normally be tested in a view context
        # Here we just verify the CSRF token generation works
        from django.test import RequestFactory

        rf = RequestFactory()
        request = rf.get("/")
        token = get_token(request)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

    @pytest.mark.unit
    def test_form_field_cleaning(self):
        """Test form field cleaning and sanitization."""

        class TestForm(forms.Form):
            name = forms.CharField(max_length=100)
            description = forms.CharField(widget=forms.Textarea)

            def clean_name(self):
                name = self.cleaned_data["name"]
                # Simulate sanitization
                return name.strip().title()

        form_data = {
            "name": "  john doe  ",
            "description": "Test description",
        }

        form = TestForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "John Doe")


class TestFormIntegration(TestCase):
    """Test form integration with models and views."""

    def setUp(self):
        """Set up test data."""
        self.site = Site.objects.create(domain="integration.example.com", name="Integration Test Site")

    @pytest.mark.unit
    def test_model_form_integration(self):
        """Test model form integration with database."""
        from django.forms import ModelForm

        class SiteForm(ModelForm):
            class Meta:
                model = Site
                fields = ["domain", "name"]

        # Create form with data
        form_data = {
            "domain": "integration2.example.com",
            "name": "Integration Test Site 2",
        }

        form = SiteForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Save to database
        site = form.save()
        self.assertIsNotNone(site.id)
        self.assertEqual(site.domain, "integration2.example.com")

        # Verify in database
        saved_site = Site.objects.get(id=site.id)
        self.assertEqual(saved_site.name, "Integration Test Site 2")

    @pytest.mark.unit
    def test_form_instance_updating(self):
        """Test updating model instances through forms."""
        from django.forms import ModelForm

        class SiteForm(ModelForm):
            class Meta:
                model = Site
                fields = ["domain", "name"]

        # Update existing site
        form_data = {
            "domain": "updated.example.com",
            "name": "Updated Site Name",
        }

        form = SiteForm(data=form_data, instance=self.site)
        self.assertTrue(form.is_valid())

        # Save changes
        form.save()
        self.site.refresh_from_db()

        self.assertEqual(self.site.domain, "updated.example.com")
        self.assertEqual(self.site.name, "Updated Site Name")


class TestFormValidationEdgeCases(TestCase):
    """Test form validation edge cases."""

    @pytest.mark.unit
    def test_empty_form_validation(self):
        """Test validation of completely empty forms."""

        class TestForm(forms.Form):
            required_field = forms.CharField(required=True)
            optional_field = forms.CharField(required=False)

        form = TestForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("required_field", form.errors)
        self.assertNotIn("optional_field", form.errors)

    @pytest.mark.unit
    def test_form_with_initial_values(self):
        """Test forms with initial values."""

        class TestForm(forms.Form):
            name = forms.CharField(initial="Default Name")
            active = forms.BooleanField(initial=True, required=False)

        # Form with no data should use initial values
        form = TestForm()
        # Check that the field has the correct initial value
        self.assertEqual(form.fields["name"].initial, "Default Name")
        self.assertEqual(form.fields["active"].initial, True)

        # Form with data should override initial values
        form = TestForm(data={"name": "Custom Name", "active": False})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "Custom Name")
        self.assertEqual(form.cleaned_data["active"], False)

    @pytest.mark.unit
    def test_form_field_dependencies(self):
        """Test forms with field dependencies."""

        class ConditionalForm(forms.Form):
            has_address = forms.BooleanField(required=False)
            address = forms.CharField(required=False)

            def clean(self):
                cleaned_data = super().clean()
                has_address = cleaned_data.get("has_address")
                address = cleaned_data.get("address")

                if has_address and not address:
                    raise ValidationError("Address is required when has_address is checked")

                return cleaned_data

        # Valid: no address needed
        form = ConditionalForm(data={"has_address": False})
        self.assertTrue(form.is_valid())

        # Valid: address provided
        form = ConditionalForm(data={"has_address": True, "address": "123 Main St"})
        self.assertTrue(form.is_valid())

        # Invalid: address required but not provided
        form = ConditionalForm(data={"has_address": True})
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
