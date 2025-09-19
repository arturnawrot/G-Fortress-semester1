class SeverityScore:
    
    def __init__(self, score: int):
        if score < 0 or score > 10:
            raise ValueError(f"SeverityScore must be between 0-10. Given {score}")
        
        self.score = score

    def get_description(self) -> str:
        if self.score >= 9:  return "CRITICAL"
        if self.score >= 7:  return "SEVERE"
        if self.score >= 4:  return "MODERATE"
        return "TRIVIAL"

    def get_color_hex(self) -> str:
        if self.score >= 9:  return "#c70808"
        if self.score >= 7:  return "#e67300"
        if self.score >= 4:  return "#d6b400"
        return "#3aa657"