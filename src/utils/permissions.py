def is_admin(user):
    return user and user.get("role") == "admin"

def can_manage_users(user):
    return user and user.get("role") in {"admin", "support_agent"}

def can_modify_plates(user):
    return user and user.get("role") in {"admin", "support_agent"}

def can_manage_issues(user):
    return user and user.get("role") in {"admin", "support_agent"}

def can_report_issues(user):
    return user and user.get("role") in {
        "admin",
        "support_agent",
        "semester_user",
        "daily_user",
        "payg_user",
    }

def can_manage_own_vehicle(user):
    return user and user.get("role") == "semester_user"