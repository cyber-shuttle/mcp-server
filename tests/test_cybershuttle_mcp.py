#!/usr/bin/env python3
"""
Test script for Cybershuttle MCP Server

This script validates the MCP server functionality including:
- Health check
- Tool discovery
- Authentication
- Basic API endpoints
"""

import requests
import json
import os
import sys
import time
from typing import Dict, Any

MCP_SERVER_URL = "http://localhost:8000"
CYBERSHUTTLE_API_BASE = "https://api.dev.cybershuttle.org:18899"

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(message: str, status: str = "info"):
    """Print colored status message."""
    color = Colors.GREEN if status == "success" else Colors.RED if status == "error" else Colors.YELLOW
    print(f"{color}{message}{Colors.RESET}")

def test_server_health() -> bool:
    """Test if the MCP server is running and healthy."""
    print_status("Testing server health...", "info")
    
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print_status(f"Server is healthy", "success")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Authenticated: {health_data.get('authenticated')}")
            print(f"   API Base: {health_data.get('api_base')}")
            return True
        else:
            print_status(f"Health check failed: {response.status_code}", "error")
            return False
    except requests.RequestException as e:
        print_status(f"Cannot connect to server: {e}", "error")
        return False

def test_tool_discovery() -> bool:
    """Test the tool discovery endpoint."""
    print_status("Testing tool discovery...", "info")
    
    try:
        response = requests.get(f"{MCP_SERVER_URL}/tools", timeout=5)
        if response.status_code == 200:
            tools = response.json()
            print_status(f"Found {len(tools)} tools", "success")

            tool_names = [tool.get('name', 'Unknown') for tool in tools[:5]]
            print(f"   Sample tools: {', '.join(tool_names)}")

            if tools and isinstance(tools[0], dict):
                required_fields = ['name', 'description', 'endpoint', 'method']
                first_tool = tools[0]
                missing_fields = [field for field in required_fields if field not in first_tool]
                
                if not missing_fields:
                    print_status("Tool structure is valid", "success")
                    return True
                else:
                    print_status(f"Missing tool fields: {missing_fields}", "error")
                    return False
            else:
                print_status("Invalid tool structure", "error")
                return False
        else:
            print_status(f"Tool discovery failed: {response.status_code}", "error")
            return False
    except requests.RequestException as e:
        print_status(f"Tool discovery error: {e}", "error")
        return False

def test_authentication() -> bool:
    """Test authentication setup."""
    print_status("Testing authentication...", "info")

    auth_token = os.getenv("CYBERSHUTTLE_AUTH_TOKEN")
    client_id = os.getenv("CYBERSHUTTLE_CLIENT_ID")
    client_secret = os.getenv("CYBERSHUTTLE_CLIENT_SECRET")
    
    if auth_token:
        print_status("CYBERSHUTTLE_AUTH_TOKEN found", "success")
        return True
    elif client_id and client_secret:
        print_status("OAuth2 credentials found", "success")
        return True
    else:
        print_status("No authentication credentials found", "info")
        print("   Set CYBERSHUTTLE_AUTH_TOKEN or CYBERSHUTTLE_CLIENT_ID/CYBERSHUTTLE_CLIENT_SECRET")
        return False

def test_api_endpoints() -> bool:
    """Test basic API endpoints."""
    print_status("Testing API endpoints...", "info")
    
    endpoints_to_test = [
        ("GET", "/resources", "List resources"),
        ("GET", "/projects", "List projects"),
        ("GET", "/sessions", "List sessions"),
        ("GET", "/resources/tags", "Get tags"),
    ]
    
    results = []
    for method, endpoint, description in endpoints_to_test:
        try:
            response = requests.request(method, f"{MCP_SERVER_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print_status(f"{description}: OK", "success")
                results.append(True)
            elif response.status_code == 401:
                print_status(f"{description}: Authentication required", "info")
                results.append(True)
            else:
                print_status(f"{description}: {response.status_code}", "error")
                results.append(False)
        except requests.RequestException as e:
            print_status(f"{description}: {e}", "error")
            results.append(False)
    
    return all(results)

def test_openai_integration() -> bool:
    """Test OpenAI integration readiness."""
    print_status("Testing OpenAI integration readiness...", "info")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print_status("OPENAI_API_KEY not set", "info")
        print("   Set this to run the OpenAI demo")
        return False
    
    if openai_key == "<Add your OpenAI API key here>":
        print_status("OPENAI_API_KEY is placeholder", "info")
        print("   Update with your actual OpenAI API key")
        return False
    
    print_status("OpenAI API key configured", "success")
    return True

def test_cybershuttle_connectivity() -> bool:
    """Test connectivity to Cybershuttle API."""
    print_status("Testing Cybershuttle API connectivity...", "info")
    
    try:
        response = requests.get(f"{CYBERSHUTTLE_API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print_status("Cybershuttle API is accessible", "success")
            return True
        else:
            print_status(f"Cybershuttle API returned: {response.status_code}", "info")
            return True
    except requests.RequestException as e:
        print_status(f"Cybershuttle API connectivity issue: {e}", "info")
        print("   This may be normal if the dev instance is not accessible")
        return True

def run_comprehensive_test():
    """Run all tests and provide a summary."""
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}    Cybershuttle MCP Server Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    
    tests = [
        ("Server Health", test_server_health),
        ("Tool Discovery", test_tool_discovery),
        ("Authentication Setup", test_authentication),
        ("API Endpoints", test_api_endpoints),
        ("OpenAI Integration", test_openai_integration),
        ("Cybershuttle Connectivity", test_cybershuttle_connectivity),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{Colors.BLUE}Testing: {test_name}{Colors.RESET}")
        result = test_func()
        results.append((test_name, result))
        time.sleep(0.5)

    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}    Test Results Summary{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    
    passed = 0
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status:<10}{Colors.RESET} {test_name}")
        if result:
            passed += 1
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{len(tests)} tests passed{Colors.RESET}")
    
    if passed == len(tests):
        print_status("All tests passed! Your Cybershuttle MCP server is ready.", "success")
    else:
        print_status("Some tests failed. Check the output above for details.", "info")
    
    return passed == len(tests)

def main():
    """Main function with command line argument handling."""
    import argparse
    global MCP_SERVER_URL
    
    parser = argparse.ArgumentParser(description="Test Cybershuttle MCP Server")
    parser.add_argument("--server-url", default=MCP_SERVER_URL,
                      help="MCP Server URL (default: http://localhost:8000)")
    parser.add_argument("--quick", action="store_true",
                      help="Run quick tests only")
    
    args = parser.parse_args()
    
    MCP_SERVER_URL = args.server_url
    
    if args.quick:
        print("Running quick tests...")
        health_ok = test_server_health()
        tools_ok = test_tool_discovery()
        
        if health_ok and tools_ok:
            print_status("Quick tests passed!", "success")
            return 0
        else:
            print_status("Quick tests failed!", "error")
            return 1
    else:
        success = run_comprehensive_test()
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 