from enum import Enum
class Visibility(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"

class Role(str, Enum):
    OWNER = "owner"
    GUEST = "guest"
