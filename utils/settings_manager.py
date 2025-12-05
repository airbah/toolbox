import json
import os
from typing import List, Dict, Any
from pathlib import Path


class SettingsManager:
    """Manages application settings stored in a JSON file."""
    
    DEFAULT_SETTINGS = {
        "invoice_companies": [
            "Amazon",
            "Google",
            "Microsoft",
            "Apple",
            "Orange",
            "Free",
            "SFR",
            "Bouygues",
            "EDF",
            "Engie",
            "OVH",
            "Scaleway",
            "Netflix",
            "Spotify",
            "Adobe",
        ],
        "invoice_min_score": 25,
    }
    
    def __init__(self):
        self.settings_dir = Path.home() / ".toolbox"
        self.settings_file = self.settings_dir / "settings.json"
        self._settings: Dict[str, Any] = {}
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from file or create default."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
            else:
                self._settings = self.DEFAULT_SETTINGS.copy()
                self._save_settings()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._settings = self.DEFAULT_SETTINGS.copy()
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value and save."""
        self._settings[key] = value
        self._save_settings()
    
    # Invoice companies specific methods
    def get_invoice_companies(self) -> List[str]:
        """Get the list of predefined invoice companies."""
        return self._settings.get("invoice_companies", [])
    
    def set_invoice_companies(self, companies: List[str]):
        """Set the list of predefined invoice companies."""
        # Clean and deduplicate
        clean_companies = []
        seen = set()
        for c in companies:
            c = c.strip()
            if c and c.lower() not in seen:
                clean_companies.append(c)
                seen.add(c.lower())
        
        self._settings["invoice_companies"] = clean_companies
        self._save_settings()
    
    def add_invoice_company(self, company: str) -> bool:
        """Add a company to the list. Returns True if added, False if already exists."""
        company = company.strip()
        if not company:
            return False
        
        companies = self.get_invoice_companies()
        if company.lower() in [c.lower() for c in companies]:
            return False
        
        companies.append(company)
        self.set_invoice_companies(companies)
        return True
    
    def remove_invoice_company(self, company: str) -> bool:
        """Remove a company from the list. Returns True if removed."""
        companies = self.get_invoice_companies()
        company_lower = company.lower()
        
        new_companies = [c for c in companies if c.lower() != company_lower]
        if len(new_companies) < len(companies):
            self.set_invoice_companies(new_companies)
            return True
        return False


# Global settings instance
settings = SettingsManager()

