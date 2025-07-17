"""
Cybershuttle MCP Server

This module implements the MCP servers and uses the endpoints in airavata's
research-service.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import requests
import os
import json
import logging
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cybershuttle MCP Server",
    description="Model Context Protocol server for Apache Cybershuttle Research Platform",
    version="1.0.0"
)

CYBERSHUTTLE_API_BASE = "https://api.dev.cybershuttle.org:18899"
CYBERSHUTTLE_AUTH_URL = f"{CYBERSHUTTLE_API_BASE}/auth"

class ResourceResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None
    tags: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    created_at: Optional[str] = None
    resources: List[str] = []

class SessionResponse(BaseModel):
    id: str
    project_id: str
    name: str
    status: str
    created_at: Optional[str] = None

class ToolInfo(BaseModel):
    name: str
    description: str
    endpoint: str
    method: str
    parameters: Dict[str, Any]
    response_schema: Dict[str, Any]

class AuthState:
    def __init__(self):
        self.token = None
        self.token_expires_at = None
        self.refresh_token = None
    
    def is_token_valid(self) -> bool:
        return (
            self.token is not None and 
            self.token_expires_at is not None and 
            datetime.now() < self.token_expires_at
        )

auth_state = AuthState()

async def get_auth_token() -> str:
    """Get a valid authentication token, refreshing if necessary."""
    if not auth_state.is_token_valid():
        await refresh_auth_token()
    
    if not auth_state.token:
        raise HTTPException(status_code=401, detail="Unable to authenticate with Cybershuttle API")
    
    return auth_state.token

async def refresh_auth_token():
    """Refresh the authentication token using device auth flow."""
    try:
        logger.info("Attempting to refresh authentication token...")
        token = os.getenv("CS_ACCESS_TOKEN")
        if not token:
            raise HTTPException(
                status_code=401,
                detail="CS_ACCESS_TOKEN environment variable not set. Please authenticate with Cybershuttle first."
            )
        
        auth_state.token = token
        auth_state.token_expires_at = datetime.now() + timedelta(hours=1)
        
        logger.info("Successfully refreshed authentication token")
        
    except Exception as e:
        logger.error(f"Failed to refresh auth token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

async def make_authenticated_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make an authenticated request to the Cybershuttle API."""
    token = await get_auth_token()
    
    headers = kwargs.get('headers', {})
    headers['Authorization'] = f'Bearer {token}'
    kwargs['headers'] = headers
    
    url = f"{CYBERSHUTTLE_API_BASE}{endpoint}"
    
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error calling {endpoint}: {e}")
        raise HTTPException(status_code=response.status_code, detail=f"Cybershuttle API error: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error calling {endpoint}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to Cybershuttle API: {e}")

# === RESOURCE CONTROLLER ENDPOINTS ===

@app.get("/resources", response_model=List[ResourceResponse])
async def list_resources(
    resource_type: Optional[str] = None,
    tags: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """List all resources (datasets, notebooks, repositories, models) from Cybershuttle catalog."""
    params = {
        "limit": limit,
        "offset": offset
    }
    if resource_type:
        params["type"] = resource_type
    if tags:
        params["tags"] = tags
    if name:
        params["name"] = name
    
    result = await make_authenticated_request("GET", "/api/v1/rf/resources/public", params=params)
    
    # Transform the response to match our model
    resources = []
    for item in result.get("content", []):
        resources.append(ResourceResponse(
            id=str(item.get("id", "")),
            name=item.get("name", ""),
            type=item.get("type", ""),
            description=item.get("description", ""),
            tags=item.get("tags", []),
            created_at=item.get("createdAt"),
            updated_at=item.get("updatedAt")
        ))
    
    return resources

@app.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(resource_id: str):
    """Get a specific resource by ID."""
    result = await make_authenticated_request("GET", f"/api/v1/rf/resources/public/{resource_id}")
    
    return ResourceResponse(
        id=str(result.get("id", "")),
        name=result.get("name", ""),
        type=result.get("type", ""),
        description=result.get("description", ""),
        tags=result.get("tags", []),
        created_at=result.get("createdAt"),
        updated_at=result.get("updatedAt")
    )

@app.post("/resources/dataset")
async def create_dataset(data: Dict[str, Any]):
    """Create a new dataset resource."""
    result = await make_authenticated_request("POST", "/api/v1/rf/resources/dataset", json=data)
    return result

@app.post("/resources/notebook")
async def create_notebook(data: Dict[str, Any]):
    """Create a new notebook resource."""
    result = await make_authenticated_request("POST", "/api/v1/rf/resources/notebook", json=data)
    return result

@app.post("/resources/repository")
async def create_repository(github_url: str):
    """Create a new repository resource."""
    result = await make_authenticated_request(
        "POST", 
        "/api/v1/rf/resources/repository", 
        params={"githubUrl": github_url}
    )
    return result

@app.post("/resources/model")
async def create_model(data: Dict[str, Any]):
    """Create a new model resource."""
    result = await make_authenticated_request("POST", "/api/v1/rf/resources/model", json=data)
    return result

@app.get("/resources/search")
async def search_resources(resource_type: str, name: str):
    """Search resources by type and name."""
    params = {"type": resource_type, "name": name}
    result = await make_authenticated_request("GET", "/api/v1/rf/resources/public/search", params=params)
    return result

@app.get("/resources/tags")
async def get_all_tags():
    """Get all available tags from the catalog."""
    result = await make_authenticated_request("GET", "/api/v1/rf/resources/public/tags/all")
    return result

# === PROJECT CONTROLLER ENDPOINTS ===

@app.get("/projects", response_model=List[ProjectResponse])
async def list_projects():
    """List all projects."""
    result = await make_authenticated_request("GET", "/api/v1/rf/projects/")
    
    projects = []
    for item in result:
        projects.append(ProjectResponse(
            id=str(item.get("id", "")),
            name=item.get("name", ""),
            description=item.get("description", ""),
            owner_id=str(item.get("ownerId", "")),
            created_at=item.get("createdAt"),
            resources=item.get("resources", [])
        ))
    
    return projects

@app.post("/projects")
async def create_project(data: Dict[str, Any]):
    """Create a new project."""
    result = await make_authenticated_request("POST", "/api/v1/rf/projects/", json=data)
    return result

@app.get("/projects/{owner_id}")
async def get_projects_by_owner(owner_id: str):
    """Get all projects by owner ID."""
    result = await make_authenticated_request("GET", f"/api/v1/rf/projects/{owner_id}")
    return result

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project by ID."""
    result = await make_authenticated_request("DELETE", f"/api/v1/rf/projects/{project_id}")
    return result

# === RESEARCH HUB CONTROLLER ENDPOINTS ===

@app.get("/hub/start-session/{project_id}")
async def start_project_session(project_id: str, session_name: str):
    """Spawn a new project session."""
    params = {"sessionName": session_name}
    result = await make_authenticated_request(
        "GET", 
        f"/api/v1/rf/hub/start/project/{project_id}", 
        params=params
    )
    return result

@app.get("/hub/resume-session/{session_id}")
async def resume_session(session_id: str):
    """Resume an existing session."""
    result = await make_authenticated_request("GET", f"/api/v1/rf/hub/resume/session/{session_id}")
    return result

# === SESSION CONTROLLER ENDPOINTS ===

@app.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(status: Optional[str] = None):
    """List all sessions, optionally filtered by status."""
    params = {}
    if status:
        params["status"] = status
    
    result = await make_authenticated_request("GET", "/api/v1/rf/sessions/", params=params)
    
    sessions = []
    for item in result:
        sessions.append(SessionResponse(
            id=str(item.get("id", "")),
            project_id=str(item.get("projectId", "")),
            name=item.get("name", ""),
            status=item.get("status", ""),
            created_at=item.get("createdAt")
        ))
    
    return sessions

@app.patch("/sessions/{session_id}")
async def update_session_status(session_id: str, status: str):
    """Update session status."""
    params = {"status": status}
    result = await make_authenticated_request(
        "PATCH", 
        f"/api/v1/rf/sessions/{session_id}", 
        params=params
    )
    return result

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    result = await make_authenticated_request("DELETE", f"/api/v1/rf/sessions/{session_id}")
    return result

# === TOOL DISCOVERY ENDPOINT ===

@app.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    """
    List all available tools/capabilities in the Cybershuttle MCP server.
    This endpoint allows LLMs and agents to discover what operations are available.
    """
    
    tools = [
        ToolInfo(
            name="list_resources",
            description="List all resources (datasets, notebooks, repositories, models) from Cybershuttle catalog with filtering options",
            endpoint="/resources",
            method="GET",
            parameters={
                "resource_type": {"type": "string", "description": "Filter by resource type (dataset, notebook, repository, model)", "optional": True},
                "tags": {"type": "string", "description": "Filter by tags", "optional": True},
                "name": {"type": "string", "description": "Filter by name", "optional": True},
                "limit": {"type": "integer", "description": "Number of results to return", "default": 10},
                "offset": {"type": "integer", "description": "Offset for pagination", "default": 0}
            },
            response_schema=ResourceResponse.schema()
        ),
        ToolInfo(
            name="get_resource",
            description="Get detailed information about a specific resource by ID",
            endpoint="/resources/{resource_id}",
            method="GET",
            parameters={
                "resource_id": {"type": "string", "description": "ID of the resource to retrieve", "required": True}
            },
            response_schema=ResourceResponse.schema()
        ),
        ToolInfo(
            name="search_resources",
            description="Search for resources by type and name",
            endpoint="/resources/search",
            method="GET",
            parameters={
                "resource_type": {"type": "string", "description": "Type of resource to search for", "required": True},
                "name": {"type": "string", "description": "Name to search for", "required": True}
            },
            response_schema={"type": "array", "items": ResourceResponse.schema()}
        ),
        ToolInfo(
            name="create_dataset",
            description="Create a new dataset resource in the catalog",
            endpoint="/resources/dataset",
            method="POST",
            parameters={
                "data": {"type": "object", "description": "Dataset metadata and configuration", "required": True}
            },
            response_schema={"type": "object", "description": "Created dataset information"}
        ),
        ToolInfo(
            name="create_notebook",
            description="Create a new notebook resource in the catalog",
            endpoint="/resources/notebook",
            method="POST",
            parameters={
                "data": {"type": "object", "description": "Notebook metadata and configuration", "required": True}
            },
            response_schema={"type": "object", "description": "Created notebook information"}
        ),
        ToolInfo(
            name="create_repository",
            description="Create a new repository resource from GitHub URL",
            endpoint="/resources/repository",
            method="POST",
            parameters={
                "github_url": {"type": "string", "description": "GitHub repository URL", "required": True}
            },
            response_schema={"type": "object", "description": "Created repository information"}
        ),
        ToolInfo(
            name="create_model",
            description="Create a new model resource in the catalog",
            endpoint="/resources/model",
            method="POST",
            parameters={
                "data": {"type": "object", "description": "Model metadata and configuration", "required": True}
            },
            response_schema={"type": "object", "description": "Created model information"}
        ),
        ToolInfo(
            name="list_projects",
            description="List all projects in the user's workspace",
            endpoint="/projects",
            method="GET",
            parameters={},
            response_schema={"type": "array", "items": ProjectResponse.schema()}
        ),
        ToolInfo(
            name="create_project",
            description="Create a new project that can contain multiple resources",
            endpoint="/projects",
            method="POST",
            parameters={
                "data": {"type": "object", "description": "Project metadata and configuration", "required": True}
            },
            response_schema={"type": "object", "description": "Created project information"}
        ),
        ToolInfo(
            name="start_project_session",
            description="Launch an interactive session for a project",
            endpoint="/hub/start-session/{project_id}",
            method="GET",
            parameters={
                "project_id": {"type": "string", "description": "ID of the project to start session for", "required": True},
                "session_name": {"type": "string", "description": "Name for the session", "required": True}
            },
            response_schema={"type": "object", "description": "Session startup information"}
        ),
        ToolInfo(
            name="list_sessions",
            description="List all active sessions",
            endpoint="/sessions",
            method="GET",
            parameters={
                "status": {"type": "string", "description": "Filter by session status", "optional": True}
            },
            response_schema={"type": "array", "items": SessionResponse.schema()}
        ),
        ToolInfo(
            name="get_all_tags",
            description="Get all available tags from the catalog for filtering and organization",
            endpoint="/resources/tags",
            method="GET",
            parameters={},
            response_schema={"type": "array", "items": {"type": "string"}}
        )
    ]
    
    return tools

# === HEALTH CHECK ===

@app.get("/health")
async def health_check():
    """Health check endpoint to verify server and API connectivity."""
    try:
        token = await get_auth_token()

        await make_authenticated_request("GET", "/api/v1/rf/resources/public/tags/all")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "api_base": CYBERSHUTTLE_API_BASE,
            "authenticated": bool(token)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "api_base": CYBERSHUTTLE_API_BASE,
            "authenticated": False
        }

# === STARTUP EVENT ===

@app.on_event("startup")
async def startup_event():
    """Initialize the server on startup."""
    logger.info("Starting Cybershuttle MCP Server...")
    logger.info(f"API Base URL: {CYBERSHUTTLE_API_BASE}")

    token = os.getenv("CS_ACCESS_TOKEN")
    if not token:
        logger.warning("CS_ACCESS_TOKEN environment variable not set.")
        logger.warning("Please set your authentication token to use the Cybershuttle API.")
    else:
        logger.info("Authentication token found. Server ready to connect to Cybershuttle API.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 