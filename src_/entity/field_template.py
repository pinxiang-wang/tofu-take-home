from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
import json  # used for deep comparison

@dataclass
class FieldTemplate:
    text: Optional[str] = None  
    url: Optional[str] = None   
    marketing_pitch: Optional[str] = None  
    crawled_content: Optional[str] = None  
    content: Optional[Any] = None   # New: store full structured content (e.g. dict)
    last_updated: Optional[str] = None  

    def has_changed(self, other: "FieldTemplate", compare_content: bool = False) -> bool:
        """
        Determine if this template has changed compared to another.
        Compares 'text', 'url', and optionally 'content'.
        """
        if self.text != other.text or self.url != other.url:
            return True
        if compare_content and self.content != other.content:
            return True
        return False
    def to_string(self) -> str:
        """
        Convert the FieldTemplate to a string.
        """
        return f"text: {self.text}, url: {self.url}, marketing_pitch: {self.marketing_pitch}, crawled_content: {self.crawled_content}, content: {self.content}, last_updated: {self.last_updated}"