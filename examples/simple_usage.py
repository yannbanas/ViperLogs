# examples/simple_usage.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from viper_logs import AdvancedLogger
from viper_logs.display import DisplayConfig

class SimpleLogger:
    """Synchronous wrapper for AdvancedLogger."""
    
    def __init__(self, service_name: str, config_path: Optional[str] = None):
        # Configuration d'affichage par défaut
        display_config = DisplayConfig(
            display_fields=["timestamp", "level", "component", "user_id", "description"],
            timestamp_format="%Y-%m-%d %H:%M:%S",
            colored_output=True
        )
        
        self.logger = AdvancedLogger(
            service_name, 
            config_path,
            display_config=display_config
        )
        
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.logger._init_cleanup_task()
    
    def log(self, level: str, user_id: str, action: str, description: str, 
            component: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """Synchronous logging method."""
        return self.loop.run_until_complete(
            self.logger.log(level, user_id, action, description, component, metadata)
        )
    
    def search_logs(self, **kwargs):
        """Synchronous log search."""
        query = self.logger.search()
        if "level" in kwargs:
            query.with_level(kwargs["level"])
        if "component" in kwargs:
            query.from_component(kwargs["component"])
        if "text" in kwargs:
            query.containing(kwargs["text"])
        if "start_time" in kwargs:
            query.in_timeframe(kwargs["start_time"])
            
        logs = self.loop.run_until_complete(self.logger.execute_search(query))
        
        # Afficher les résultats en format tableau
        print("\nSearch Results:")
        print(self.logger.display_config.format_log_table(logs))
        return logs
    
    def close(self):
        """Clean up resources."""
        try:
            self.loop.run_until_complete(self.logger.close())
        finally:
            self.loop.close()

if __name__ == "__main__":
    # Create logger
    logger = SimpleLogger("simple_example")
    
    try:
        # Basic logging - ligne simple
        log_id = logger.log(
            "INFO",
            "user123",
            "test",
            "Testing simple logger with new display",
            "example"
        )
        
        # Test different log levels
        logger.log("DEBUG", "user123", "debug", "Debug message", "authentication")
        logger.log("WARN", "user456", "warning", "Warning message", "database")
        logger.log("ERROR", "admin", "error", "Error message", "api")
        
        # Search and display logs in table format
        logs = logger.search_logs(
            level="INFO"
        )
    
    finally:
        logger.close()