"""
Dynamic CSS Context Processor for Preferences Pages
Provides theme and styling context to templates
"""


def preferences_theme_context(request):
    """
    Add theme and styling context to all templates.
    This allows dynamic CSS control across all preferences pages.
    """
    # Get theme from session, cookie, or user preference
    theme = None
    custom_primary = None
    custom_accent = None

    if hasattr(request, "user") and request.user.is_authenticated:
        # Try to get theme from user profile
        if hasattr(request.user, "profile"):
            theme = getattr(request.user.profile, "preferred_theme", None)
            custom_primary = getattr(request.user.profile, "custom_primary_color", None)
            custom_accent = getattr(request.user.profile, "custom_accent_color", None)

    # Fall back to session or cookie
    if not theme:
        theme = request.session.get("preferences_theme", request.COOKIES.get("preferences_theme", "default"))

    # Get animations preference
    animations = True
    if hasattr(request, "user") and request.user.is_authenticated:
        if hasattr(request.user, "profile"):
            animations = getattr(request.user.profile, "enable_animations", True)

    if not isinstance(animations, bool):
        animations = request.session.get("preferences_animations", True)

    # Detect user preferences from browser
    user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
    is_mobile = any(device in user_agent for device in ["mobile", "android", "iphone"])

    # High contrast mode detection (would need JavaScript for full detection)
    high_contrast = request.GET.get("high_contrast") == "1"

    context = {
        "preferences_theme": {
            "current": theme,
            "animations_enabled": animations,
            "is_mobile": is_mobile,
            "high_contrast": high_contrast,
            "available_themes": [
                {
                    "id": "default",
                    "name": "Default",
                    "description": "Original home page colors",
                },
                {"id": "dark", "name": "Dark", "description": "Dark green theme"},
                {"id": "light", "name": "Light", "description": "Light blue theme"},
            ],
        },
        "css_variables": {
            "primary_color": custom_primary or ("#663333" if theme == "default" else "#2c5530" if theme == "dark" else "#4a90e2"),
            "accent_color": custom_accent or ("#CCCC66" if theme == "default" else "#5a9c66" if theme == "dark" else "#f0a500"),
        },
    }

    return context
