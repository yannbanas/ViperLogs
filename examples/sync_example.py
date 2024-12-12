# examples/sync_example.py
"""Example of synchronous usage of the logger."""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from viper_logs import AdvancedLogger
from viper_logs.search import LogQuery
from datetime import datetime, timedelta

def main():
    # Create logger
    logger = AdvancedLogger("example_service")
    
    # Create event loop
    loop = asyncio.get_event_loop()
    
    # Example 1: Basic logging
    log_id = loop.run_until_complete(
        logger.log("INFO", "user123", "login", "User logged in successfully", "auth")
    )
    print(f"Log created with ID: {log_id}")
    
    # Example 2: Search logs
    query = logger.search()\
        .with_level("INFO")\
        .from_component("auth")\
        .containing("success")
    
    logs = loop.run_until_complete(logger.execute_search(query))
    print("\nFound logs:", len(logs))
    for log in logs:
        print(f"- {log['timestamp']}: {log['description']}")
    
    # Example 3: Analyze logs
    analysis = loop.run_until_complete(
        logger.analyze_logs(timeframe=timedelta(hours=1))
    )
    print("\nLog analysis:", analysis)
    
    # Clean up
    loop.run_until_complete(logger.close())
    loop.close()

if __name__ == "__main__":
    main()