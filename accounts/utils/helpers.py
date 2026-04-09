import re
from rest_framework.exceptions import ValidationError

def validate_phone_number(phone):
    """
    Validates the phone number format (+91XXXXXXXXXX) or (XXXXXXXXXX)
    """
    if not phone:
        raise ValidationError({"phone": "Phone number is required."})
        
    # If it's just 10 digits, add +91
    if re.match(r'^\d{10}$', phone):
        phone = f"+91{phone}"
        
    pattern = r'^\+91\d{10}$'
    if not re.match(pattern, phone):
        raise ValidationError({"phone": "Phone number must be 10 digits (with or without +91 prefix)."})
    return phone
