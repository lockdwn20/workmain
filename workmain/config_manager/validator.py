"""
WorkmAIn
Configuration Validator v0.1.0
20251219

Validate configuration files against schemas
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re


class ValidationError(Exception):
    """Configuration validation error"""
    pass


class ConfigValidator:
    """Validate configuration files"""
    
    # Define schemas for each config file
    SCHEMAS = {
        "ai_settings": {
            "default_provider": {"type": "string", "required": True, "values": ["claude", "gemini"]},
            "providers": {"type": "dict", "required": True},
            "per_report_override": {"type": "dict", "required": False},
            "fallback": {"type": "dict", "required": False},
            "cost_tracking": {"type": "dict", "required": False},
        },
        "notifications": {
            "enabled": {"type": "boolean", "required": True},
            "timezone": {"type": "string", "required": True},
            "method": {"type": "string", "required": True, "values": ["terminal", "os", "email"]},
            "work_hours": {"type": "dict", "required": True},
            "schedule": {"type": "list", "required": True},
        },
        "database": {
            "host": {"type": "string", "required": False},
            "port": {"type": "string", "required": False},
            "name": {"type": "string", "required": False},
            "user": {"type": "string", "required": False},
            "password": {"type": "string", "required": False},
        },
    }
    
    @staticmethod
    def validate_type(value: Any, expected_type: str) -> bool:
        """
        Validate value type
        
        Args:
            value: Value to validate
            expected_type: Expected type name
            
        Returns:
            True if type matches
        """
        type_map = {
            "string": str,
            "integer": int,
            "boolean": bool,
            "dict": dict,
            "list": list,
            "float": float,
        }
        
        expected_class = type_map.get(expected_type)
        if expected_class is None:
            return False
        
        return isinstance(value, expected_class)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid email format
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_time(time_str: str) -> bool:
        """
        Validate time format (HH:MM in 24-hour format)
        
        Args:
            time_str: Time string to validate
            
        Returns:
            True if valid time format
        """
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """
        Validate date format (YYYY-MM-DD)
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid date format
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    def validate_config(
        self,
        config_name: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Validate configuration against schema
        
        Args:
            config_name: Name of configuration
            config: Configuration dict to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Get schema for this config
        schema = self.SCHEMAS.get(config_name)
        if schema is None:
            # No schema defined, skip validation
            return errors
        
        # Check required fields
        for field_name, field_schema in schema.items():
            if field_schema.get("required", False):
                if field_name not in config:
                    errors.append(f"Missing required field: {field_name}")
                    continue
            
            # Skip if field not present and not required
            if field_name not in config:
                continue
            
            value = config[field_name]
            
            # Validate type
            expected_type = field_schema.get("type")
            if expected_type and not self.validate_type(value, expected_type):
                errors.append(
                    f"Field '{field_name}' has wrong type. "
                    f"Expected {expected_type}, got {type(value).__name__}"
                )
            
            # Validate allowed values
            allowed_values = field_schema.get("values")
            if allowed_values and value not in allowed_values:
                errors.append(
                    f"Field '{field_name}' has invalid value '{value}'. "
                    f"Allowed values: {allowed_values}"
                )
        
        return errors
    
    def validate_all(self, configs: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Validate all configurations
        
        Args:
            configs: Dict mapping config names to their contents
            
        Returns:
            Dict mapping config names to lists of error messages
        """
        all_errors = {}
        
        for config_name, config in configs.items():
            errors = self.validate_config(config_name, config)
            if errors:
                all_errors[config_name] = errors
        
        return all_errors
    
    def validate_recipients(self, recipients: List[str]) -> List[str]:
        """
        Validate list of email recipients
        
        Args:
            recipients: List of email addresses
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for email in recipients:
            if not self.validate_email(email):
                errors.append(f"Invalid email address: {email}")
        
        return errors
    
    def validate_notification_schedule(self, schedule: Dict[str, Any]) -> List[str]:
        """
        Validate notification schedule entry
        
        Args:
            schedule: Schedule entry dict
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Required fields
        required_fields = ["id", "time", "enabled", "days", "message"]
        for field in required_fields:
            if field not in schedule:
                errors.append(f"Missing required field in schedule: {field}")
        
        # Validate time format
        if "time" in schedule:
            if not self.validate_time(schedule["time"]):
                errors.append(f"Invalid time format: {schedule['time']} (expected HH:MM)")
        
        # Validate days
        valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if "days" in schedule:
            for day in schedule["days"]:
                if day.lower() not in valid_days:
                    errors.append(f"Invalid day: {day}")
        
        return errors


# Global validator instance
_validator = None


def get_validator() -> ConfigValidator:
    """
    Get global configuration validator instance
    
    Returns:
        ConfigValidator instance
    """
    global _validator
    if _validator is None:
        _validator = ConfigValidator()
    return _validator
