"""Configuration module for advanced logger."""
from pathlib import Path
from typing import Dict, Optional
import yaml
import json

class LogConfig:
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        if not config_path:
            return self._default_config()
            
        path = Path(config_path)
        with path.open() as f:
            return yaml.safe_load(f) if path.suffix == '.yaml' else json.load(f)
            
    def _default_config(self) -> Dict:
        return {
            # Paramètres de base
            "log_dir": "logs",
            "rotation_size": 5 * 1024 * 1024,  # 5 MB
            "locale": "en",
            "default_level": "INFO",
            
            # Paramètres de performance
            "buffer_size": 100,
            "retention_days": 30,
            
            # Paramètres de sécurité
            "sensitive_fields": ["password", "token", "key", "secret"],
            "similarity_threshold": 0.85,
            
            # Paramètres API
            "api_enabled": True,
            "api_port": 8000,
            "api_host": "0.0.0.0",
            
            # Paramètres de stockage
            "storage_mode": "local",  # "local" ou "remote"
            "remote_url": None,  # URL pour le stockage distant
            
            # Paramètres des métriques
            "metrics_enabled": True,
            "metrics_retention": 7,  # jours de rétention des métriques
            
            # Paramètres d'affichage
            "display_format": "SHORT",  # "SHORT", "DETAILED", ou "FULL"
            
            # Paramètres de compression
            "compression_enabled": True,
            "compression_algorithm": "gzip"  # "gzip" ou "zip"
        }

    def update_config(self, new_config: Dict) -> None:
        """Met à jour la configuration avec de nouvelles valeurs."""
        self.config.update(new_config)

    def save_config(self, config_path: str) -> None:
        """Sauvegarde la configuration actuelle dans un fichier."""
        path = Path(config_path)
        with path.open('w') as f:
            if path.suffix == '.yaml':
                yaml.dump(self.config, f)
            else:
                json.dump(self.config, f, indent=2)

    def validate_config(self) -> bool:
        """Valide la configuration actuelle."""
        required_fields = ["log_dir", "default_level"]
        return all(field in self.config for field in required_fields)