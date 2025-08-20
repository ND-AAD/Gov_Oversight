"""RFP data model for storing procurement opportunities."""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib
import json


@dataclass
class RFP:
    """
    Represents a Request for Proposal (RFP) from a government website.
    
    Core model that stores all extracted information about procurement opportunities,
    with emphasis on tracking changes and categorizing potential surveillance contracts.
    """
    
    # Core identification (required fields first)
    id: str
    title: str
    url: str
    source_site: str
    posted_date: str
    
    # Extracted data (flexible structure for different sites)
    extracted_fields: Dict[str, Any]
    
    # Metadata
    detected_at: datetime
    content_hash: str
    categories: List[str]
    
    # Optional fields with defaults (must come after required fields)
    closing_date: Optional[str] = None
    description: str = ""
    change_history: Optional[List[Dict[str, Any]]] = field(default=None)
    manual_review_status: Optional[str] = None  # 'pending', 'reviewed', 'flagged'
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate and process RFP data after initialization."""
        if not self.content_hash:
            self.content_hash = self.generate_content_hash()
        
        if self.change_history is None:
            self.change_history = []
            
        # Ensure categories is always a list
        if isinstance(self.categories, str):
            self.categories = [self.categories]
    
    def generate_content_hash(self) -> str:
        """Generate a hash of the RFP content for change detection."""
        content = f"{self.title}:{self.url}:{json.dumps(self.extracted_fields, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def add_change_record(self, field: str, old_value: Any, new_value: Any) -> None:
        """Record a change to this RFP for audit trail."""
        change_record = {
            'timestamp': datetime.now().isoformat(),
            'field': field,
            'old_value': str(old_value) if old_value is not None else None,
            'new_value': str(new_value) if new_value is not None else None
        }
        
        if self.change_history is None:
            self.change_history = []
        
        self.change_history.append(change_record)
    
    def update_field(self, field: str, new_value: Any) -> bool:
        """
        Update an extracted field and record the change.
        
        Returns True if the value actually changed, False otherwise.
        """
        old_value = self.extracted_fields.get(field)
        
        if old_value != new_value:
            self.extracted_fields[field] = new_value
            self.add_change_record(field, old_value, new_value)
            
            # Update content hash
            old_hash = self.content_hash
            self.content_hash = self.generate_content_hash()
            
            return True
        
        return False
    
    def get_display_value(self, field: str, default: str = "N/A") -> str:
        """Get a human-readable display value for a field."""
        value = self.extracted_fields.get(field, default)
        
        if value is None:
            return default
            
        # Handle common field types
        if field.lower() in ['posted_date', 'closing_date', 'deadline']:
            try:
                if isinstance(value, str):
                    # Try to parse and reformat date
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime('%B %d, %Y')
            except:
                pass
        
        elif field.lower() in ['contract_value', 'value', 'amount']:
            try:
                # Try to format as currency
                if isinstance(value, str):
                    # Remove currency symbols and commas for parsing
                    clean_value = value.replace('$', '').replace(',', '')
                    amount = float(clean_value)
                    return f"${amount:,.0f}"
            except:
                pass
        
        return str(value)
    
    def is_high_priority(self) -> bool:
        """Determine if this RFP should be flagged as high priority."""
        high_priority_categories = [
            'surveillance', 'security', 'biometric', 'facial_recognition',
            'data_collection', 'intelligence', 'monitoring'
        ]
        
        # Check categories
        for category in self.categories:
            if category.lower() in high_priority_categories:
                return True
        
        # Check title and description for keywords
        text_to_check = f"{self.title} {self.extracted_fields.get('description', '')}"
        high_priority_keywords = [
            'facial recognition', 'biometric', 'surveillance', 'monitoring',
            'intelligence', 'predictive policing', 'social media monitoring',
            'cell site simulator', 'stingray', 'IMSI catcher', 'mass surveillance'
        ]
        
        text_lower = text_to_check.lower()
        for keyword in high_priority_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def is_closing_soon(self, days_threshold: int = 7) -> bool:
        """Check if RFP is closing within the specified number of days."""
        closing_date_str = self.extracted_fields.get('closing_date')
        if not closing_date_str:
            return False
        
        try:
            closing_date = datetime.fromisoformat(closing_date_str.replace('Z', '+00:00'))
            days_until_closing = (closing_date - datetime.now()).days
            return 0 <= days_until_closing <= days_threshold
        except:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert RFP to dictionary for JSON serialization."""
        data = asdict(self)
        
        # Convert datetime objects to ISO strings
        if isinstance(data['detected_at'], datetime):
            data['detected_at'] = data['detected_at'].isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RFP':
        """Create RFP instance from dictionary."""
        # Convert ISO string back to datetime
        if isinstance(data.get('detected_at'), str):
            data['detected_at'] = datetime.fromisoformat(data['detected_at'].replace('Z', '+00:00'))
        
        return cls(**data)
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"RFP({self.id}): {self.title} from {self.source_site}"
    
    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (f"RFP(id='{self.id}', title='{self.title[:50]}...', "
                f"source_site='{self.source_site}', categories={self.categories})")
