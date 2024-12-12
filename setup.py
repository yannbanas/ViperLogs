# setup.py
from setuptools import setup, find_packages

setup(
    name="viper_logs",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "pyyaml>=6.0.0"
    ],
    author="BANAS Yann",
    description="Modern Python logging library",
    python_requires=">=3.9.0",
)