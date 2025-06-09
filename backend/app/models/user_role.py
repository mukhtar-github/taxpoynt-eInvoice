import enum

class UserRole(str, enum.Enum):
    """
    Enumeration of user roles in the system.
    These roles determine permissions and access levels.
    """
    OWNER = "owner"     # Organization owner with full permissions
    ADMIN = "admin"     # Administrator with elevated permissions
    MEMBER = "member"   # Regular organization member
    SI_USER = "si_user" # System Integrator User
