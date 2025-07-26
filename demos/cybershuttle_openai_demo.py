import openai
import requests
import json
import os
from typing import Dict, Any, List

client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "<Add your OpenAI API key here>")
)

MCP_SERVER_URL = "http://127.0.0.1:8000"

functions = [
    {
        "name": "list_resources",
        "description": "List all resources (datasets, notebooks, repositories, models) from Cybershuttle catalog with filtering options",
        "parameters": {
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "Filter by resource type (dataset, notebook, repository, model)",
                    "enum": ["dataset", "notebook", "repository", "model"]
                },
                "tags": {
                    "type": "string",
                    "description": "Filter by tags"
                },
                "name": {
                    "type": "string",
                    "description": "Filter by name"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_resource",
        "description": "Get detailed information about a specific resource by ID",
        "parameters": {
            "type": "object",
            "properties": {
                "resource_id": {
                    "type": "string",
                    "description": "ID of the resource to retrieve"
                }
            },
            "required": ["resource_id"]
        }
    },
    {
        "name": "search_resources",
        "description": "Search for resources by type and name",
        "parameters": {
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "Type of resource to search for",
                    "enum": ["dataset", "notebook", "repository", "model"]
                },
                "name": {
                    "type": "string",
                    "description": "Name to search for"
                }
            },
            "required": ["resource_type", "name"]
        }
    },
    {
        "name": "create_dataset",
        "description": "Create a new dataset resource in the catalog",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Dataset metadata and configuration",
                    "properties": {
                        "name": {"type": "string", "description": "Dataset name"},
                        "description": {"type": "string", "description": "Dataset description"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"}
                    }
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "create_notebook",
        "description": "Create a new notebook resource in the catalog",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Notebook metadata and configuration",
                    "properties": {
                        "name": {"type": "string", "description": "Notebook name"},
                        "description": {"type": "string", "description": "Notebook description"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"}
                    }
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "create_repository",
        "description": "Create a new repository resource from GitHub URL",
        "parameters": {
            "type": "object",
            "properties": {
                "github_url": {
                    "type": "string",
                    "description": "GitHub repository URL"
                }
            },
            "required": ["github_url"]
        }
    },
    {
        "name": "create_model",
        "description": "Create a new model resource in the catalog",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Model metadata and configuration",
                    "properties": {
                        "name": {"type": "string", "description": "Model name"},
                        "description": {"type": "string", "description": "Model description"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"}
                    }
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "list_projects",
        "description": "List all projects in the user's workspace",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "create_project",
        "description": "Create a new project that can contain multiple resources",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Project metadata and configuration",
                    "properties": {
                        "name": {"type": "string", "description": "Project name"},
                        "description": {"type": "string", "description": "Project description"}
                    }
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "start_project_session",
        "description": "Launch an interactive session for a project",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "ID of the project to start session for"
                },
                "session_name": {
                    "type": "string",
                    "description": "Name for the session"
                }
            },
            "required": ["project_id", "session_name"]
        }
    },
    {
        "name": "list_sessions",
        "description": "List all active sessions",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by session status"
                }
            }
        }
    },
    {
        "name": "get_all_tags",
        "description": "Get all available tags from the catalog for filtering and organization",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]

def call_mcp_function(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Call a function on the Cybershuttle MCP server."""
    try:
        endpoint_map = {
            "list_resources": "/resources",
            "get_resource": "/resources/{resource_id}",
            "search_resources": "/resources/search",
            "create_dataset": "/resources/dataset",
            "create_notebook": "/resources/notebook",
            "create_repository": "/resources/repository",
            "create_model": "/resources/model",
            "list_projects": "/projects",
            "create_project": "/projects",
            "start_project_session": "/hub/start-session/{project_id}",
            "list_sessions": "/sessions",
            "get_all_tags": "/resources/tags"
        }
        
        method_map = {
            "list_resources": "GET",
            "get_resource": "GET",
            "search_resources": "GET",
            "create_dataset": "POST",
            "create_notebook": "POST",
            "create_repository": "POST",
            "create_model": "POST",
            "list_projects": "GET",
            "create_project": "POST",
            "start_project_session": "GET",
            "list_sessions": "GET",
            "get_all_tags": "GET"
        }
        
        endpoint = endpoint_map.get(function_name)
        method = method_map.get(function_name)
        
        if not endpoint or not method:
            return {"error": f"Unknown function: {function_name}"}

        url = f"{MCP_SERVER_URL}{endpoint}"

        if function_name == "get_resource":
            url = url.format(resource_id=parameters.get("resource_id"))
            params = {}
        elif function_name == "start_project_session":
            url = url.format(project_id=parameters.get("project_id"))
            params = {"session_name": parameters.get("session_name")}
        elif function_name == "create_repository":
            params = {"github_url": parameters.get("github_url")}
        else:
            if method == "GET":
                params = parameters
            else:
                params = {}

        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            if function_name in ["create_dataset", "create_notebook", "create_model", "create_project"]:
                response = requests.post(url, json=parameters.get("data"))
            else:
                response = requests.post(url, params=params)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API call failed with status {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": f"Failed to call MCP function: {str(e)}"}

def display_resources(resources: List[Dict[str, Any]]) -> str:
    """Format resources for display."""
    if not resources:
        return "No resources found."
    
    formatted = "\n**Cybershuttle Resources:**\n"
    for resource in resources:
        formatted += f"• **{resource.get('name', 'Unknown')}** ({resource.get('type', 'Unknown')})\n"
        formatted += f"  {resource.get('description', 'No description')}\n"
        formatted += f"  Tags: {', '.join(resource.get('tags', []))}\n"
        formatted += f"  ID: {resource.get('id')}\n\n"
    
    return formatted

def display_projects(projects: List[Dict[str, Any]]) -> str:
    """Format projects for display."""
    if not projects:
        return "No projects found."
    
    formatted = "\n**Cybershuttle Projects:**\n"
    for project in projects:
        formatted += f"• **{project.get('name', 'Unknown')}**\n"
        formatted += f"  {project.get('description', 'No description')}\n"
        formatted += f"  Owner: {project.get('owner_id')}\n"
        formatted += f"  ID: {project.get('id')}\n\n"
    
    return formatted

def display_sessions(sessions: List[Dict[str, Any]]) -> str:
    """Format sessions for display."""
    if not sessions:
        return "No sessions found."
    
    formatted = "\n**Active Sessions:**\n"
    for session in sessions:
        formatted += f"• **{session.get('name', 'Unknown')}**\n"
        formatted += f"  Status: {session.get('status')}\n"
        formatted += f"  Project: {session.get('project_id')}\n"
        formatted += f"  ID: {session.get('id')}\n\n"
    
    return formatted

def main():
    """Main interactive loop for the Cybershuttle MCP demo."""
    print("Welcome to the Cybershuttle MCP Demo!")
    print("This demo showcases how an AI agent can interact with the Cybershuttle research platform.")
    print("You can ask questions about datasets, notebooks, models, projects, and sessions.")
    print("Type 'exit' to quit.\n")

    example_prompts = [
        "Show me all datasets in the catalog",
        "Find notebooks related to machine learning",
        "Create a new project for my research",
        "List all active sessions",
        "Search for repositories about deep learning",
        "What tags are available in the catalog?",
        "Start a session for project XYZ"
    ]
    
    print("Example prompts you can try:")
    for i, prompt in enumerate(example_prompts, 1):
        print(f"   {i}. {prompt}")
    print()
    
    while True:
        user_message = input("You: ")
        
        if user_message.lower() in ['exit', 'quit', 'bye']:
            print("Thank you for using the Cybershuttle MCP Demo!")
            break
        
        if not user_message.strip():
            continue
        
        print("AI Agent: Processing your request...")
        
        try:
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are an AI assistant specialized in helping researchers interact with the Cybershuttle research platform. 
                        You can help users find, create, and manage datasets, notebooks, models, repositories, projects, and sessions.
                        Always be helpful and provide clear, actionable responses. When displaying results, format them nicely for readability.
                        If you need to call multiple functions to fulfill a request, do so systematically."""
                    },
                    {"role": "user", "content": user_message}
                ],
                functions=functions,
                function_call="auto",
                max_tokens=1000
            )
            
            message = response.choices[0].message

            if message.function_call:
                func_call = message.function_call
                print(f"Calling function: {func_call.name}")

                try:
                    args = json.loads(func_call.arguments)
                except json.JSONDecodeError:
                    print("Error: Invalid function arguments")
                    continue
                
                function_result = call_mcp_function(func_call.name, args)
                
                if "error" in function_result:
                    print(f"Error: {function_result['error']}")
                    continue

                formatted_result = ""
                if func_call.name == "list_resources":
                    formatted_result = display_resources(function_result)
                elif func_call.name == "list_projects":
                    formatted_result = display_projects(function_result)
                elif func_call.name == "list_sessions":
                    formatted_result = display_sessions(function_result)
                elif func_call.name == "get_all_tags":
                    if isinstance(function_result, list):
                        # Commenting out my implementation and using Sutej's
                        # formatted_result = f"**Available Tags:** {', '.join(function_result)}"
                        formatted_result = f"**Available Tags:** {', '.join(tag.get('value', '') for tag in function_result)}"
                    else:
                        formatted_result = f"**Available Tags:** {function_result}"
                else:
                    formatted_result = json.dumps(function_result, indent=2)

                followup = client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {
                            "role": "system", 
                            "content": """You are an AI assistant for the Cybershuttle research platform. 
                            Provide helpful, conversational responses about the results. Be encouraging and offer suggestions for next steps."""
                        },
                        {"role": "user", "content": user_message},
                        {
                            "role": "function",
                            "name": func_call.name,
                            "content": formatted_result
                        }
                    ],
                    max_tokens=500
                )
                
                print(f"Results:\n{formatted_result}")
                print(f"\nAI Agent: {followup.choices[0].message.content}")
                
            else:
                print(f"AI Agent: {message.content}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Please try again or type 'exit' to quit.")
        
        print()

if __name__ == "__main__":
    main() 