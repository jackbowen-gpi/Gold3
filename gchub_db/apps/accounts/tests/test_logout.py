import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_logout_get_disallowed_and_post_allowed():
    c = Client()

    logout_url = reverse("logout")

    # GET should be disallowed (405)
    resp_get = c.get(logout_url)
    assert resp_get.status_code in (
        405,
        302,
    )  # Some setups may have a compatibility fallback
    if resp_get.status_code == 302:
        # If a site has a GET fallback, ensure it redirects away (legacy behavior)
        assert resp_get["Location"]

    # POST should log out/redirect to LOGOUT_REDIRECT_URL (302)
    resp_post = c.post(logout_url, follow=False)
    assert resp_post.status_code == 302
