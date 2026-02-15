import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    LEGAL_REPRESENTATIVE = "legal_representative"
    USER = "user"