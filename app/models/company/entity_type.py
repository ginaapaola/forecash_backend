import enum


class EntityType(str, enum.Enum):
    NATURAL = "natural"
    LEGAL = "legal"