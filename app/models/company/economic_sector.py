import enum


class EconomicSector(str, enum.Enum):
    PRIMARY = "primary"
    INDUSTRIAL = "industrial"
    SERVICES = "services"