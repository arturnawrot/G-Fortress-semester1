class Machine:
    VALID_OPERATING_SYSTEMS = {"windows", "linux"}

    def __init__(self, friendly_name: str, operating_system: str):
        operating_system = operating_system.lower()
        if operating_system not in self.VALID_OPERATING_SYSTEMS:
            raise ValueError(f"Invalid operating_system: '{operating_system}'. Must be one of {self.VALID_OPERATING_SYSTEMS}.")
        
        self.friendly_name = friendly_name
        self.operating_system = operating_system