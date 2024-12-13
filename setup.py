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
    author_email="yannbanas@gmail.com",
    description="Modern Python logging library",
    long_description=open("readme.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yannbanas/ViperLogs",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
)