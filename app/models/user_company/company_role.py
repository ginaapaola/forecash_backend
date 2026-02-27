from enum import Enum


class CompanyRole(str, Enum):
    LEGAL_REPRESENTATIVE = "legal_representative"
    USER = "user"