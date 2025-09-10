from django.urls import re_path as url

from gchub_db.apps.django_su.views import su_exit, su_login, login_as_user

urlpatterns = [
    url(r"^$", su_exit, name="su_exit"),
    url(r"^login/$", su_login, name="su_login"),
    url(r"^(?P<user_id>[\d]+)/$", login_as_user, name="login_as_user"),
]
