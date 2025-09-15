from neontology import BaseNode

class User(BaseNode):
    __primarylabel__ = "User"
    __primaryproperty__ = "username"
    username: str
    hashed_password: str