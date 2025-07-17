"""
Cybershuttle MCP Server Package

This package provides a Model Context Protocol (MCP) server for Apache Cybershuttle.
It enables AI agents to interact with the Cybershuttle research catalog through
natural language queries and operations.

Main Components:
- cybershuttle_mcp_server: Main MCP server implementation
- cybershuttle_auth: OAuth2 authentication handler
"""

__version__ = "1.0.0"
__author__ = "Apache Airavata Team"
__email__ = "dev@airavata.apache.org"

try:
    from .cybershuttle_mcp_server import app
    from .cybershuttle_auth import CybershuttleAuth
except ImportError:
    pass

__all__ = ["app", "CybershuttleAuth"] 