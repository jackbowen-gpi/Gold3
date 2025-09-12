"""
This middleware stores certain information for use outside areas in the
codebase that can't typically reach said information.

For example, if a model has a last_modified_by field related to the User model,
over-riding the save() method on the model would result in having no way to
get to the User ID that last saved the object.
"""

from threading import local

_thread_locals = local()


def get_current_user():
    return getattr(_thread_locals, "user", None)


class ThreadLocals(object):
    """
    Middleware that gets various objects from the
    request object and saves them in thread local storage.

    Also stores some useful information on the UserProfile object.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user:
            # If this is an authenticated user, do some tracking.
            if user.is_authenticated:
                # UserProfile stores the user's last IP address.
                profile = user.profile
                ip_address = request.META["REMOTE_ADDR"]
                # Only update this when there's a new address to save writes.
                if ip_address != profile.ip_address:
                    profile.ip_address = ip_address
                    profile.save()
            # Store the newly saved User.
            _thread_locals.user = user

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    # Process Request does not appear to be used any more as of DJango 1.10
    def process_request(self, request):
        user = getattr(request, "user", None)
        if user:
            # If this is an authenticated user, do some tracking.
            if user.is_authenticated:
                # UserProfile stores the user's last IP address.
                profile = user.profile
                ip_address = request.META["REMOTE_ADDR"]
                # Only update this when there's a new address to save writes.
                if ip_address != profile.ip_address:
                    profile.ip_address = ip_address
                    profile.save()
            # Store the newly saved User.
            _thread_locals.user = user
