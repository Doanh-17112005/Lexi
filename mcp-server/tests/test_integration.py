"""Test basic MCP server functionality"""

import pytest
import asyncio
import sys
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters


@pytest.mark.asyncio
async def test_mcp_server_startup():
    """Test that MCP server starts and responds"""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Server should respond to initialization
            assert session is not None


@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available tools"""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            
            # This server is intentionally limited to coding-time IDE tools;
            # app runtime AI/voice capabilities live in ai-service.
            assert set(tool_names) == {
                "manage_i18n_key",
                "search_web",
                "get_backend_schema",
                "list_flutter_screens",
            }


@pytest.mark.asyncio
async def test_list_resources():
    """Test listing available resources"""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            resources = await session.list_resource_templates()
            resource_uris = [r.uriTemplate for r in resources.resourceTemplates]
            
            # Check that core resources are available
            assert any("learner_profile" in uri for uri in resource_uris)
            assert any("conversation" in uri for uri in resource_uris)


@pytest.mark.asyncio
async def test_flutter_screen_tool():
    """Test a local IDE tool without an external AI provider."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "list_flutter_screens",
                {},
            )
            
            assert result.content
            assert len(result.content) > 0
            # Response should be JSON string
            import json
            response = json.loads(result.content[0].text)
            assert (
                "total_screens" in response and "by_feature" in response
            ) or "error" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
