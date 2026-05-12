def is_admin(user):
    return user and user.get("role") == "admin"


def is_support_agent(user):
    return user and user.get("role") == "support_agent"


def is_parking_officer(user):
    return user and user.get("role") == "parking_officer"


def can_manage_users(user):
    return is_admin(user)


def can_manage_issues(user):
    return user and user.get("role") in {
        "admin",
        "support_agent",
        "parking_officer",
    }


def can_modify_plates(user):
    return user and user.get("role") in {
        "admin",
        "parking_officer",
    }


def can_view_logs(user):
    return user and user.get("role") in {
        "admin",
        "support_agent",
    }


def can_reset_password(user):
    return user and user.get("role") in {
        "admin",
        "support_agent",
    }