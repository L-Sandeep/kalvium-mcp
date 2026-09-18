from setuptools import setup, find_packages


setup(
    name="kalvium-mcp",
    version="2.0.0.dev0",
    description="Authenticated MCP server for Kalvium",
    py_modules=[
        "server",
        "auth",
        "browser",
        "tools",
        "scraper",
        "markdown",
    ],
    packages=find_packages(),
)