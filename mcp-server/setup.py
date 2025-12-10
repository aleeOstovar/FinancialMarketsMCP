from setuptools import setup, find_packages

setup(
    name="mcp-server",
    version="0.1.0",
    # This tells Python to treat 'src' as a package, preserving your import structure
    packages=find_packages(), 
    install_requires=[
        "fastmcp",
        "requests",
        "pydantic",
        "pydantic-settings",
        "python-dotenv"
    ]
)