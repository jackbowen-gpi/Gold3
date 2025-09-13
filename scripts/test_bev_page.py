"""
Quick functional check that a beverage job page renders for the dev test user.

Run to perform a simple Django test client request and print basic results.
"""


def run():
    """
    Execute a small Django test client request and print basic results.

    Useful as a quick smoke test during local development.
    """
    from django.test import Client

    # Use the dev user created earlier
    c = Client()
    logged = c.login(username="devtester", password="password")
    print("logged in:", logged)
    # Provide HTTP_HOST to avoid DisallowedHost from the test client default
    resp = c.get("/workflow/job/new/beverage/", HTTP_HOST="127.0.0.1:8002")
    print("status_code:", resp.status_code)
    content = resp.content.decode("utf-8", errors="replace")
    # Print a small snippet to confirm form is present
    start = content.find("<title")
    print("title snippet:")
    print(content[start : start + 200])
    # Also print whether form tag exists
    print("contains_form_tag:", "<form" in content)
