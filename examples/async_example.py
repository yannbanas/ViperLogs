# examples/async_example.py
"""Example of asynchronous usage of the logger."""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from viper_logs import AdvancedLogger
from viper_logs.search import LogQuery
from datetime import datetime, timedelta

async def main():
    # Create logger
    logger = AdvancedLogger("example_service")
    
    # Example 1: Basic logging
    log_id = await logger.log(
        "INFO", 
        "user123", 
        "login", 
        "User logged in successfully", 
        "auth"
    )
    print(f"Log created with ID: {log_id}")
    
    # Example 2: Multiple logs
    tasks = []
    for i in range(3):
        task = logger.log(
            "INFO",
            f"user{i}",
            "action",
            f"Example action {i}",
            "example"
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    # Example 3: Search logs
    query = logger.search()\
        .with_level("INFO")\
        .from_component("auth")\
        .containing("success")
    
    logs = await logger.execute_search(query)
    print("\nFound logs:", len(logs))
    for log in logs:
        print(f"- {log['timestamp']}: {log['description']}")
    
    # Example 4: Analyze logs
    analysis = await logger.analyze_logs(timeframe=timedelta(hours=1))
    print("\nLog analysis:", analysis)
    
    # Clean up
    await logger.close()

# Run the async example
if __name__ == "__main__":
    asyncio.run(main())
