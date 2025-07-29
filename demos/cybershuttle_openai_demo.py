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
        "description": "List all resources (datasets, notebooks, repositories, models) from Cybershuttle catalog with filtering options. For domain-specific searches, use appropriate tags: neuroscience→neurodata25, ML→brainml, vision→image-classification, NLP→natural-language-processing",
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
                    "description": "Filter by tags (use: neurodata25 for neuroscience, brainml for ML, image-classification for vision)"
                },
                "name": {
                    "type": "string",
                    "description": "Filter by name"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 15
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
        "description": "Search for resources by content relevance using name matching. Use keywords from user's query as search terms.",
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
                    "description": "Search term extracted from user query (e.g., 'DeepSeek', 'machine learning', 'neural networks')"
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
    },
    {
    "name": "search_projects",
    "description": "Search for research projects by keywords, topics, or research areas",
    "parameters": {
        "type": "object", 
        "properties": {
            "search_term": {
                "type": "string",
                "description": "Search term for project names, descriptions, or associated research topics"
            }
        },
        "required": ["search_term"]
    }
}
]

def call_mcp_function(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Call a function on the Cybershuttle MCP server."""
    try:
        endpoint_map = {
            "list_resources": "/resources",
            "get_resource": "/resources/{resource_id}",
            "search_resources": "/resources",
            "create_dataset": "/resources/dataset",
            "create_notebook": "/resources/notebook",
            "create_repository": "/resources/repository",
            "create_model": "/resources/model",
            "list_projects": "/projects",
            "create_project": "/projects",
            "search_projects": "/projects",
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
            "search_projects": "GET",
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
        elif function_name == "search_resources":
            params = {
                "resource_type": parameters.get("resource_type", "").lower(),
                "name": parameters.get("name", "")
            }
        elif function_name == "search_projects":
            response = requests.get(f"{MCP_SERVER_URL}/projects")
            if response.status_code == 200:
                all_projects = response.json()
                search_term = parameters.get("search_term", "").lower()
                
                semantic_params = get_semantic_search_params(search_term)
                print(f"DEBUG: search_term='{search_term}', semantic_params={semantic_params}")

                if "tags" in semantic_params:
                    target_tag = semantic_params["tags"].lower()
                    print(f"DEBUG: Looking for tag: {target_tag}")
                else:
                    target_tag = search_term
                
                filtered = []
                for project in all_projects:
                    project_matched = False

                    if (search_term in project.get("name", "").lower() or 
                        search_term in project.get("description", "").lower()):
                        filtered.append(project)
                        print(f"DEBUG: Matched by name/desc: {project.get('name')}")
                        continue

                    repo = project.get("repositoryResource", {})
                    if repo and "tags" in repo:
                        repo_tags = [tag.get("value", "").lower() for tag in repo["tags"]]
                        print(f"DEBUG: Project '{project.get('name')}' repo tags: {repo_tags}")
                        if target_tag in repo_tags or any(search_term in tag for tag in repo_tags):
                            filtered.append(project)
                            print(f"DEBUG: Matched by repo tags: {project.get('name')}")
                            project_matched = True

                    if not project_matched:
                        datasets = project.get("datasetResources", [])
                        for dataset in datasets:
                            if "tags" in dataset:
                                dataset_tags = [tag.get("value", "").lower() for tag in dataset["tags"]]
                                print(f"DEBUG: Project '{project.get('name')}' dataset tags: {dataset_tags}")
                                if target_tag in dataset_tags or any(search_term in tag for tag in dataset_tags):
                                    filtered.append(project)
                                    print(f"DEBUG: Matched by dataset tags: {project.get('name')}")
                                    break
                
                print(f"DEBUG: Found {len(filtered)} matching projects")
                return filtered
            else:
                return {"error": f"Failed to search projects: {response.text}"}
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
    """Format resources for display with enhanced metadata."""
    if not resources:
        return "No resources found."
    
    formatted = "\n**Cybershuttle Resources:**\n"
    for resource in resources:
        formatted += f"• **{resource.get('name', 'Unknown')}** ({resource.get('type', 'Unknown')})\n"
        formatted += f"  {resource.get('description', 'No description')}\n"

        authors = resource.get('authors', [])
        if authors:
            formatted += f"  👥 Authors: {', '.join(authors)}\n"

        status = resource.get('status')
        if status:
            formatted += f"  📊 Status: {status}\n"

        repo_url = resource.get('repository_url')
        if repo_url:
            formatted += f"  🔗 Repository: {repo_url}\n"
 
        dataset_url = resource.get('dataset_url')
        if dataset_url:
            formatted += f"  📂 Dataset: {dataset_url}\n"
        
        formatted += f"  🏷️ Tags: {', '.join(resource.get('tags', []))}\n"
        formatted += f"  🆔 ID: {resource.get('id')}\n\n"
    
    return formatted

def display_projects(projects: List[Dict[str, Any]]) -> str:
    """Format projects for display with enhanced metadata."""
    if not projects:
        return "No projects found."
    
    formatted = "\n**Cybershuttle Projects:**\n"
    for project in projects:
        formatted += f"• **{project.get('name', 'Unknown')}**\n"
        formatted += f"  📝 Description: {project.get('description', 'No description')}\n"
        formatted += f"  👤 Owner: {project.get('owner_id')}\n"

        repo_resource = project.get('repository_resource')
        dataset_resources = project.get('dataset_resources', [])
        
        resource_info = []
        if repo_resource:
            resource_info.append("1 repository")
        if dataset_resources:
            resource_info.append(f"{len(dataset_resources)} dataset(s)")
        
        if resource_info:
            formatted += f"  📊 Resources: {', '.join(resource_info)}\n"

        state = project.get('state')
        if state:
            formatted += f"  🔄 State: {state}\n"
        
        formatted += f"  🆔 ID: {project.get('id')}\n\n"
    
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

def display_specific_resource(resource: Dict[str, Any]) -> str:
    """Format a single resource with full enhanced details."""
    formatted = f"\n**🎯 Found Resource: {resource.get('name')}**\n"
    formatted += f"**Type:** {resource.get('type')}\n"
    formatted += f"**Description:** {resource.get('description', 'No description')}\n"

    authors = resource.get('authors', [])
    if authors:
        formatted += f"**👥 Authors:** {', '.join(authors)}\n"
    
    status = resource.get('status')
    if status:
        formatted += f"**📊 Status:** {status}\n"
    
    state = resource.get('state')
    if state:
        formatted += f"**🔄 State:** {state}\n"
    
    repo_url = resource.get('repository_url')
    if repo_url:
        formatted += f"**🔗 Repository:** {repo_url}\n"
    
    dataset_url = resource.get('dataset_url')
    if dataset_url:
        formatted += f"**📂 Dataset:** {dataset_url}\n"
    
    formatted += f"**🏷️ Tags:** {', '.join(resource.get('tags', []))}\n"
    formatted += f"**🆔 ID:** {resource.get('id')}\n"
    
    return formatted

def display_filtered_projects(projects: List[Dict[str, Any]], criteria: str) -> str:
    """Format projects with filtering context."""
    if not projects:
        return f"No projects found matching '{criteria}'."
    
    formatted = f"\n**🔍 Projects matching '{criteria}' ({len(projects)} found):**\n"
    for project in projects:
        formatted += f"• **{project.get('name')}**\n"
        formatted += f"  Owner: {project.get('owner_id')}\n"
        formatted += f"  Resources: {len(project.get('dataset_resources', []))} datasets"
        if project.get('repository_resource'):
            formatted += ", 1 repository"
        formatted += "\n"
        if hasattr(project, 'all_tags'):
            formatted += f"  Tags: {', '.join(project.all_tags[:5])}\n"
        formatted += "\n"
    
    return formatted

def get_semantic_search_params(query: str) -> dict:
    """Convert natural language queries to search parameters."""
    query_lower = query.lower()

    if any(term in query_lower for term in ['neuroscience', 'brain', 'neural', 'neuro']):
        return {"tags": "neurodata25"}

    if any(term in query_lower for term in ['machine learning', 'ml', 'deep learning']):
        return {"tags": "brainml"}

    if any(term in query_lower for term in ['computer vision', 'image', 'visual']):
        return {"tags": "image-classification"}

    if any(term in query_lower for term in ['nlp', 'natural language', 'language processing']):
        return {"tags": "natural-language-processing"}

    return {"name": query}


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
                        
                        IMPORTANT TAG MAPPINGS for better search results:
                        - "neuroscience" or "brain research" → use tags="neurodata25"
                        - "machine learning" or "ML" → use tags="brainml" 
                        - "deep learning" → use tags="llm" or search for "neural"
                        - "computer vision" → use tags="image-classification" or "visual_cortex"
                        - "natural language processing" → use tags="natural-language-processing" or "llm"
                        
                        When users ask for datasets/repositories "about X", use the list_resources function with appropriate tags or name filters.
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
                elif func_call.name == "search_resources":
                    if len(function_result) == 1:
                        formatted_result = display_specific_resource(function_result[0])
                    else:
                        formatted_result = display_resources(function_result)
                elif func_call.name == "list_projects":
                    formatted_result = display_projects(function_result)
                elif func_call.name == "search_projects":
                    search_term = args.get("search_term", "unknown")
                    formatted_result = display_filtered_projects(function_result, search_term)
                elif func_call.name == "list_sessions":
                    formatted_result = display_sessions(function_result)
                elif func_call.name == "get_all_tags":
                    if isinstance(function_result, list):
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