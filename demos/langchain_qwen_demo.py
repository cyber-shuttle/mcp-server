"""
Cybershuttle LangChain + Qwen3 Demo

This demo showcases enhanced research discovery capabilities using:
- LangChain for intelligent tool orchestration
- Qwen3 (via Ollama) for cost-effective, customizable LLM
- Enhanced reasoning for better research discovery
- Semantic understanding of research domains
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

import langchain
import langchain_ollama
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain.schema import AgentAction, AgentFinish
from langchain.callbacks.base import BaseCallbackHandler

OLLAMA_MODEL = "qwen3:8b"
MCP_SERVER_URL = "http://127.0.0.1:8000"

class ResearchCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for research-focused logging."""
    
    def on_agent_action(self, action: AgentAction, **kwargs):
        print(f"🔍 **Research Action**: {action.tool}")
        print(f"   Input: {action.tool_input}")
    
    def on_agent_finish(self, finish: AgentFinish, **kwargs):
        print(f"✅ **Research Complete**")

class CybershuttleLangChainTools:
    """LangChain-compatible tools for Cybershuttle MCP integration."""
    
    def __init__(self):
        self.mcp_url = MCP_SERVER_URL
    
    def _call_mcp_api(self, method: str, endpoint: str, params: Dict = None, json_data: Dict = None) -> Dict[str, Any]:
        """Make API call to MCP server."""
        try:
            url = f"{self.mcp_url}{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, json=json_data, params=params)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API call failed: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def enhanced_semantic_search(self, query: str) -> Dict[str, str]:
        """Enhanced semantic search parameter mapping with domain intelligence."""
        query_lower = query.lower()

        if any(term in query_lower for term in [
            'neuroscience', 'brain', 'neural', 'neuro', 'cortex', 'synapse',
            'cognitive', 'fmri', 'eeg', 'neuroimaging', 'connectome'
        ]):
            return {"tags": "neurodata25", "domain": "neuroscience"}

        if any(term in query_lower for term in [
            'machine learning', 'ml', 'deep learning', 'neural network',
            'tensorflow', 'pytorch', 'transformer', 'llm', 'gpt'
        ]):
            return {"tags": "brainml", "domain": "machine_learning"}

        if any(term in query_lower for term in [
            'computer vision', 'image', 'visual', 'opencv', 'cnn',
            'classification', 'detection', 'segmentation'
        ]):
            return {"tags": "image-classification", "domain": "computer_vision"}

        if any(term in query_lower for term in [
            'nlp', 'natural language', 'text', 'language processing',
            'sentiment', 'tokenization', 'embedding'
        ]):
            return {"tags": "natural-language-processing", "domain": "nlp"}

        if any(term in query_lower for term in [
            'data science', 'analytics', 'statistics', 'pandas',
            'visualization', 'jupyter', 'python'
        ]):
            return {"name": query, "domain": "data_science"}
        
        # default fallback
        return {"name": query, "domain": "general"}
    
    def list_resources_tool(self, query: str) -> str:
        """Enhanced resource listing with intelligent filtering."""
        search_params = self.enhanced_semantic_search(query)

        resource_type = None
        if "dataset" in query.lower():
            resource_type = "dataset"
        elif "notebook" in query.lower():
            resource_type = "notebook"
        elif "repository" in query.lower() or "repo" in query.lower():
            resource_type = "repository"
        elif "model" in query.lower():
            resource_type = "model"

        params = {"pageNumber": 0, "pageSize": 100}
        if resource_type:
            params["resource_type"] = resource_type
        if "tags" in search_params:
            params["tags"] = search_params["tags"]
        if "name" in search_params:
            params["name"] = search_params["name"]
        
        result = self._call_mcp_api("GET", "/resources", params=params)
        
        if "error" in result:
            return f"Error: {result['error']}"

        domain = search_params.get("domain", "general")
        formatted = f"🔬 **{domain.title().replace('_', ' ')} Resources** ({len(result)} found)\n\n"
        
        for resource in result[:15]:
            formatted += f"• **{resource.get('name', 'Unknown')}** ({resource.get('type', 'Unknown')})\n"
            formatted += f"  📝 {resource.get('description', 'No description')[:100]}...\n"
            
            if resource.get('authors'):
                formatted += f"  👥 Authors: {', '.join(resource['authors'][:3])}\n"
            
            if resource.get('status'):
                formatted += f"  📊 Status: {resource['status']}\n"
            
            if resource.get('repository_url'):
                formatted += f"  🔗 {resource['repository_url']}\n"
            
            formatted += f"  🏷️ {', '.join(resource.get('tags', [])[:5])}\n"
            formatted += f"  🆔 {resource.get('id')}\n\n"
        
        return formatted
    
    def search_projects_tool(self, query: str) -> str:
        """Enhanced project search with semantic understanding."""
        search_params = self.enhanced_semantic_search(query)

        result = self._call_mcp_api("GET", "/projects")
        
        if "error" in result:
            return f"Error: {result['error']}"

        filtered_projects = []
        search_term = query.lower()
        target_tag = search_params.get("tags", "").lower()
        
        for project in result:
            if (search_term in project.get("name", "").lower() or 
                search_term in project.get("description", "").lower()):
                filtered_projects.append(project)
                continue

            if target_tag:
                repo = project.get("repositoryResource", {})
                if repo and "tags" in repo:
                    repo_tags = [tag.get("value", "").lower() for tag in repo["tags"]]
                    if target_tag in repo_tags:
                        filtered_projects.append(project)
                        continue

                for dataset in project.get("datasetResources", []):
                    if "tags" in dataset:
                        dataset_tags = [tag.get("value", "").lower() for tag in dataset["tags"]]
                        if target_tag in dataset_tags:
                            filtered_projects.append(project)
                            break

        domain = search_params.get("domain", "general")
        formatted = f"🏗️ **{domain.title().replace('_', ' ')} Projects** ({len(filtered_projects)} found)\n\n"
        
        for project in filtered_projects[:10]:
            formatted += f"• **{project.get('name', 'Unknown')}**\n"
            formatted += f"  📝 {project.get('description', 'No description')[:150]}...\n"
            formatted += f"  👤 Owner: {project.get('owner_id')}\n"

            repo_count = 1 if project.get('repositoryResource') else 0
            dataset_count = len(project.get('datasetResources', []))
            formatted += f"  📊 Resources: {repo_count} repository, {dataset_count} datasets\n"
            
            formatted += f"  🆔 {project.get('id')}\n\n"
        
        return formatted
    
    def get_resource_details_tool(self, resource_id: str) -> str:
        """Get detailed resource information."""
        result = self._call_mcp_api("GET", f"/resources/{resource_id}")
        
        if "error" in result:
            return f"Error: {result['error']}"

        formatted = f"🎯 **Resource Details: {result.get('name')}**\n\n"
        formatted += f"**Type**: {result.get('type')}\n"
        formatted += f"**Description**: {result.get('description', 'No description')}\n\n"
        
        if result.get('authors'):
            formatted += f"**👥 Authors**: {', '.join(result['authors'])}\n"
        
        if result.get('status'):
            formatted += f"**📊 Status**: {result['status']}\n"
        
        if result.get('repository_url'):
            formatted += f"**🔗 Repository**: {result['repository_url']}\n"
        
        if result.get('dataset_url'):
            formatted += f"**📂 Dataset**: {result['dataset_url']}\n"
        
        formatted += f"**🏷️ Tags**: {', '.join(result.get('tags', []))}\n"
        
        if result.get('created_at'):
            formatted += f"**📅 Created**: {result['created_at']}\n"
        
        formatted += f"**🆔 ID**: {result.get('id')}\n"
        
        return formatted
    
    def create_resource_tool(self, resource_data: str) -> str:
        """Create a new resource (dataset, notebook, model, or repository)."""
        try:
            if resource_data.startswith('{'):
                data = json.loads(resource_data)
            else:
                return "Error: Please provide resource data in JSON format"
            
            resource_type = data.get('type', '').lower()
            
            if resource_type == 'repository':
                github_url = data.get('github_url') or data.get('url')
                if not github_url:
                    return "Error: Repository creation requires 'github_url'"
                result = self._call_mcp_api("POST", "/resources/repository", params={"github_url": github_url})
            elif resource_type in ['dataset', 'notebook', 'model']:
                result = self._call_mcp_api("POST", f"/resources/{resource_type}", json_data=data)
            else:
                return f"Error: Unsupported resource type '{resource_type}'. Use: dataset, notebook, model, repository"
            
            if "error" in result:
                return f"Error creating resource: {result['error']}"
            
            return f"✅ Successfully created {resource_type}: {result.get('name', 'Unknown')}"
            
        except json.JSONDecodeError:
            return "Error: Invalid JSON format in resource data"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_research_tags_tool(self, domain: str = "") -> str:
        """Get available research tags with domain organization."""
        result = self._call_mcp_api("GET", "/resources/tags")
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        if not isinstance(result, list):
            return "Error: Unexpected response format"

        tags = []
        for tag in result:
            if isinstance(tag, dict):
                tags.append(tag.get('value', ''))
            else:
                tags.append(str(tag))
        
        domain_tags = {
            'neuroscience': [t for t in tags if any(k in t.lower() for k in ['neuro', 'brain', 'cortex'])],
            'machine_learning': [t for t in tags if any(k in t.lower() for k in ['ml', 'learning', 'neural'])],
            'computer_vision': [t for t in tags if any(k in t.lower() for k in ['image', 'visual', 'cv'])],
            'nlp': [t for t in tags if any(k in t.lower() for k in ['language', 'text', 'nlp'])],
            'general': [t for t in tags if not any(k in t.lower() for k in ['neuro', 'brain', 'ml', 'image', 'language'])]
        }
        
        formatted = "🏷️ **Research Tags by Domain**\n\n"
        
        for domain_name, domain_tag_list in domain_tags.items():
            if domain_tag_list:
                formatted += f"**{domain_name.title().replace('_', ' ')}**:\n"
                formatted += f"  {', '.join(domain_tag_list[:10])}\n\n"
        
        return formatted
    
    def get_tools(self) -> List[Tool]:
        """Get all LangChain tools for the Cybershuttle MCP integration."""
        return [
            Tool(
                name="list_resources",
                description="Search and list research resources (datasets, notebooks, repositories, models). Use keywords like 'neuroscience', 'machine learning', 'computer vision' for domain-specific results.",
                func=self.list_resources_tool
            ),
            Tool(
                name="search_projects",
                description="Search for research projects by domain, topic, or keywords. Understands research domains and semantic search.",
                func=self.search_projects_tool
            ),
            Tool(
                name="get_resource_details",
                description="Get detailed information about a specific resource using its ID.",
                func=self.get_resource_details_tool
            ),
            Tool(
                name="create_resource",
                description="Create a new research resource. Provide JSON data with type (dataset/notebook/model/repository) and details.",
                func=self.create_resource_tool
            ),
            Tool(
                name="get_research_tags",
                description="Get all available research tags organized by domain for better discovery and filtering.",
                func=self.get_research_tags_tool
            )
        ]

def create_research_agent() -> AgentExecutor:
    """Create a LangChain agent specialized for research discovery."""
    
    # initializing Qwen3 via Ollama
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        temperature=0.1,
        base_url="http://localhost:11434"
    )
    
    # getting Cybershuttle tools
    cybershuttle_tools = CybershuttleLangChainTools()
    tools = cybershuttle_tools.get_tools()

    research_prompt = PromptTemplate.from_template("""
    You are an advanced AI research assistant specializing in scientific discovery and data exploration. 
    You help researchers find datasets, notebooks, models, repositories, and projects from the Cybershuttle research platform.

    You have access to powerful tools for:
    - Searching resources with semantic understanding of research domains
    - Finding projects related to specific research areas
    - Getting detailed information about research artifacts
    - Creating new research resources
    - Understanding available research tags and domains

    Key research domains you understand:
    - Neuroscience & Brain Research (use 'neurodata25' tag)
    - Machine Learning & AI (use 'brainml' tag) 
    - Computer Vision (use 'image-classification' tag)
    - Natural Language Processing (use 'natural-language-processing' tag)
    - Data Science & Analytics

    When helping users:
    1. Understand their research domain and intent
    2. Use semantic search to find relevant resources
    3. Provide rich, detailed information with context
    4. Suggest related resources and next steps
    5. Format results clearly with emojis and structure

    Available tools: {tool_names}
    Tool descriptions: {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: think about what you need to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question with rich formatting

    Begin!

    Question: {input}
    Thought: {agent_scratchpad}
    """
    )

    agent = create_react_agent(llm, tools, research_prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        callbacks=[ResearchCallbackHandler()],
        max_iterations=5,
        handle_parsing_errors=True
    )
    
    return agent_executor

def main():
    """Main interactive loop for the LangChain + Qwen3 demo."""
    print("🚀 **Cybershuttle LangChain + Qwen3 Research Assistant**")
    print("=" * 60)
    print("Enhanced research discovery with intelligent semantic understanding!")
    print("Powered by LangChain + Qwen3 (via Ollama)")
    print()
    
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server connected")
        else:
            print("⚠️  Ollama server not responding. Please ensure Ollama is running.")
            print("   Run: ollama serve")
            return
    except requests.RequestException:
        print("❌ Cannot connect to Ollama. Please ensure it's installed and running.")
        print("   Install: curl -fsSL https://ollama.ai/install.sh | sh")
        print("   Pull model: ollama pull qwen3:8b")
        print("   Start server: ollama serve")
        return
    
    # Initialize agent
    print("🤖 Initializing Qwen3 research agent...")
    try:
        agent = create_research_agent()
        print("✅ Agent ready!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    print()
    print("**Example Research Queries:**")
    example_queries = [
        "Find neuroscience datasets with brain imaging data",
        "Show me machine learning projects with neural networks", 
        "What computer vision repositories are available?",
        "Create a new dataset for my climate research project",
        "Find all notebooks related to data visualization",
        "What research tags are available for natural language processing?"
    ]
    
    for i, query in enumerate(example_queries, 1):
        print(f"   {i}. {query}")
    
    print("\nType 'exit' to quit, 'help' for more examples.\n")
    
    while True:
        try:
            user_input = input("🔬 Research Query: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Thank you for using the Cybershuttle Research Assistant! 🚀")
                break
            
            if user_input.lower() == 'help':
                print("**Advanced Research Queries You Can Try:**")
                advanced_queries = [
                    "Compare machine learning datasets vs neuroscience datasets",
                    "Find the most recent repositories in computer vision",
                    "What projects combine neuroscience and machine learning?",
                    "Show me all resources created by specific authors",
                    "Find datasets that have both 'neural' and 'imaging' tags"
                ]
                for query in advanced_queries:
                    print(f"   • {query}")
                print()
                continue
            
            if not user_input:
                continue
            
            print("\n🧠 **Qwen3 Agent Processing...**")
            print("-" * 40)
            
            # Run the agent
            result = agent.invoke({"input": user_input})
            
            print("\n" + "="*60)
            print("🎯 **Research Results:**")
            print("="*60)
            print(result['output'])
            print("="*60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting... Thank you for using the Research Assistant! 🚀")
            break
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            print("Please try again or type 'help' for examples.\n")

if __name__ == "__main__":
    try:
        print(f"Using LangChain version: {langchain.__version__}")
    except ImportError as e:
        print("❌ Missing required packages. Install with:")
        print("pip install langchain langchain-ollama")
        exit(1)
    
    main()