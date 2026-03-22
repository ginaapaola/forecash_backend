import enum


class RegimeType(str, enum.Enum):
    SIMPLE = "simple"
    ORDINARY = "ordinary"
    NONE = "none"