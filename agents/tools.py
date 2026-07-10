"""Compatibility module for the original project shape.

The enhanced build keeps direct tool logic out of agent nodes. Agents call MCP
tools through agents.mcp_client instead, so providers can be swapped without
editing the graph.
"""
