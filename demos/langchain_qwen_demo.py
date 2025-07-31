"""
Cybershuttle LangChain + Qwen3 Demo - Robust & Simple Version

This demo focuses on reliability and simplicity:
- Direct API calls matching your MCP server exactly
- No unnecessary complexity or extra tools
- Robust search that handles all query types
- Clean, simple tool architecture
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
    """Simple, robust tools for Cybershuttle MCP integration."""
    
    def __init__(self):
        self.mcp_url = MCP_SERVER_URL
    
    def _call_mcp_api(self, method: str, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API call to MCP server with proper error handling."""
        try:
            url = f"{self.mcp_url}{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=10)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            if response.status_code == 200:
                result = response.json()
                # Always return the result as-is (your MCP server returns lists directly)
                return result if result else []
            else:
                return {"error": f"API call failed: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def search_resources(self, query: str) -> str:
        """Main resource search tool - handles all resource discovery."""
        
        # Clean the input properly - remove quotes and extra whitespace
        query_clean = query.strip().strip('"').strip("'").lower()
        
        # Determine if looking for specific resource type
        resource_type = None
        if "repository" in query_clean or "repositories" in query_clean:
            resource_type = "repository"
        elif "dataset" in query_clean or "datasets" in query_clean:
            resource_type = "dataset"
        elif "notebook" in query_clean or "notebooks" in query_clean:
            resource_type = "notebook"
        elif "model" in query_clean or "models" in query_clean:
            resource_type = "model"
        else:
            resource_type= "repository,notebook,dataset,model"
        
        # Extract search terms properly (preserve case for API calls)
        original_query = query.strip().strip('"').strip("'")
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'find', 'show', 'me', 'get', 'are', 'there', 'any'}
        
        # Split and clean, but preserve original case
        words = []
        for w in original_query.replace(',', ' ').replace('.', ' ').replace('?', ' ').split():
            if w.lower() not in stop_words and len(w) > 1:
                words.append(w)
        
        print(f"🔍 Original query: '{original_query}'")
        print(f"🔍 Search terms: {words}")
        print(f"🔍 Resource type filter: {resource_type}")
        
        all_results = []
        search_attempts = []
        
        # Strategy 1: Try exact multi-word phrases first (most specific)
        if len(words) >= 2:
            # Try the full phrase
            full_phrase = ' '.join(words)
            params = {"name": full_phrase}
            if resource_type:
                params["resource_type"] = resource_type
            
            print(f"🔍 Trying full phrase: '{full_phrase}'")
            result = self._call_mcp_api("GET", "/resources", params=params)
            
            if isinstance(result, list):
                if result:  # Non-empty list
                    all_results.extend(result)
                    search_attempts.append(f"phrase '{full_phrase}' -> {len(result)} results")
                else:
                    search_attempts.append(f"phrase '{full_phrase}' -> 0 results")
            elif "error" in result:
                search_attempts.append(f"phrase '{full_phrase}' -> error: {result['error']}")
            
            # Try 2-word combinations
            for i in range(len(words) - 1):
                phrase = ' '.join(words[i:i+2])
                if phrase != full_phrase:  # Don't repeat the full phrase
                    params = {"name": phrase}
                    if resource_type:
                        params["resource_type"] = resource_type
                    
                    print(f"🔍 Trying 2-word phrase: '{phrase}'")
                    result = self._call_mcp_api("GET", "/resources", params=params)
                    
                    if isinstance(result, list):
                        if result:
                            all_results.extend(result)
                            search_attempts.append(f"phrase '{phrase}' -> {len(result)} results")
                        else:
                            search_attempts.append(f"phrase '{phrase}' -> 0 results")
                    elif "error" in result:
                        search_attempts.append(f"phrase '{phrase}' -> error: {result['error']}")
        
        # Strategy 2: Try individual significant terms (preserve case)
        for word in words:
            if len(word) > 2:  # Skip very short words
                params = {"name": word}
                if resource_type:
                    params["resource_type"] = resource_type
                
                print(f"🔍 Trying individual term: '{word}'")
                result = self._call_mcp_api("GET", "/resources", params=params)
                
                if isinstance(result, list):
                    if result:
                        all_results.extend(result)
                        search_attempts.append(f"term '{word}' -> {len(result)} results")
                    else:
                        search_attempts.append(f"term '{word}' -> 0 results")
                elif "error" in result:
                    search_attempts.append(f"term '{word}' -> error: {result['error']}")
        
        # Strategy 3: Try common domain tags only if no results yet
        if not all_results:
            domain_tags = []
            if any(term in query_clean for term in ['neuroscience', 'brain', 'neural', 'neuro']):
                domain_tags.append('neurodata25')
            if any(term in query_clean for term in ['machine learning', 'ml']):
                domain_tags.append('brainml')
            if any(term in query_clean for term in ['visual', 'cortex', 'vision']):
                domain_tags.append('visual_cortex')
            if any(term in query_clean for term in ['nlp', 'language', 'text']):
                domain_tags.append('natural-language-processing')
            if any(term in query_clean for term in ['computer vision', 'image', 'resnet']):
                domain_tags.append('image-classification')
                domain_tags.append('resnet')
            
            for tag in domain_tags:
                params = {"tags": tag}
                if resource_type:
                    params["resource_type"] = resource_type
                
                print(f"🔍 Trying tag: '{tag}'")
                result = self._call_mcp_api("GET", "/resources", params=params)
                
                if isinstance(result, list):
                    if result:
                        all_results.extend(result)
                        search_attempts.append(f"tag '{tag}' -> {len(result)} results")
                    else:
                        search_attempts.append(f"tag '{tag}' -> 0 results")
                elif "error" in result:
                    search_attempts.append(f"tag '{tag}' -> error: {result['error']}")
        
        # Remove duplicates by ID
        unique_results = []
        seen_ids = set()
        for item in all_results:
            if isinstance(item, dict):
                item_id = item.get('id')
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    unique_results.append(item)
        
        print(f"🔍 Search attempts made: {search_attempts}")
        print(f"🔍 Unique results found: {len(unique_results)}")
        
        if not unique_results:
            return f"❌ No resources found for '{original_query}'\n\nSearch attempts made:\n" + "\n".join(search_attempts) + "\n\nTry different keywords or check spelling."
        
        # Format results cleanly
        formatted = f"🔬 **Found {len(unique_results)} Resource(s) for '{query}'**\n\n"
        
        for i, resource in enumerate(unique_results[:10], 1):  # Show top 10
            name = resource.get('name', 'Unknown')
            res_type = resource.get('type', 'Unknown')
            description = resource.get('description', 'No description')
            
            formatted += f"{i}. **{name}** ({res_type})\n"
            formatted += f"   📝 {description[:120]}{'...' if len(description) > 120 else ''}\n"
            
            # Authors
            authors = resource.get('authors', [])
            if authors:
                formatted += f"   👥 Authors: {', '.join(authors[:3])}\n"
            
            # Status/State (only if meaningful)
            status = resource.get('status')
            if status and status != 'NONE':
                formatted += f"   📊 Status: {status}\n"
                
            state = resource.get('state')
            if state and state != 'ACTIVE':
                formatted += f"   🔄 State: {state}\n"
            
            # URLs
            repo_url = resource.get('repository_url')
            if repo_url:
                formatted += f"   🔗 Repository: {repo_url}\n"
                
            dataset_url = resource.get('dataset_url')
            if dataset_url:
                formatted += f"   📂 Dataset: {dataset_url}\n"
            
            # Tags (cleaned up)
            tags = resource.get('tags', [])
            if tags:
                formatted += f"   🏷️ Tags: {', '.join(tags[:5])}\n"
            
            # Creation date (simplified)
            created = resource.get('created_at')
            if created:
                date_part = created.split('T')[0] if 'T' in created else created
                formatted += f"   📅 Created: {date_part}\n"
            
            formatted += f"   🆔 ID: {resource.get('id')}\n\n"
        
        if len(unique_results) > 10:
            formatted += f"... and {len(unique_results) - 10} more results.\n"
        
        return formatted
    
    def search_projects(self, query: str) -> str:
        """Search for research projects."""

        result = self._call_mcp_api("GET", "/projects")
        
        if "error" in result:
            return f"Error searching projects: {result['error']}"
        
        if not isinstance(result, list) or not result:
            return "No projects found in the system."
        
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]

        scored_projects = []
        
        for project in result:
            score = 0
            project_name = project.get("name", "").lower()
            project_desc = project.get("description", "").lower()
            
            for word in query_words:
                if word in project_name:
                    score += 10
                elif word in project_desc:
                    score += 5

            repo_resource = project.get("repositoryResource", {})
            if repo_resource and "tags" in repo_resource:
                repo_tags = [tag.get("value", "").lower() for tag in repo_resource["tags"]]
                for word in query_words:
                    if any(word in tag for tag in repo_tags):
                        score += 3
            
            for dataset in project.get("datasetResources", []):
                if "tags" in dataset:
                    dataset_tags = [tag.get("value", "").lower() for tag in dataset["tags"]]
                    for word in query_words:
                        if any(word in tag for tag in dataset_tags):
                            score += 2
            
            if score > 0:
                scored_projects.append((project, score))

        scored_projects.sort(key=lambda x: x[1], reverse=True)
        
        if not scored_projects:
            return f"❌ No projects found matching '{query}'"

        formatted = f"🏗️ **Found {len(scored_projects)} Project(s) for '{query}'**\n\n"
        
        for i, (project, score) in enumerate(scored_projects[:8], 1):
            name = project.get('name', 'Unknown')
            description = project.get('description', 'No description')
            owner = project.get('owner_id', 'Unknown')
            
            formatted += f"{i}. **{name}** (relevance: {score})\n"
            formatted += f"   📝 {description[:120]}{'...' if len(description) > 120 else ''}\n"
            formatted += f"   👤 Owner: {owner}\n"

            repo_count = 1 if project.get('repositoryResource') else 0
            dataset_count = len(project.get('datasetResources', []))
            formatted += f"   📊 Resources: {repo_count} repository, {dataset_count} datasets\n"
            
            formatted += f"   🆔 ID: {project.get('id')}\n\n"
        
        return formatted
    
    def get_available_tags(self, domain: str = "") -> str:
        """Get all available research tags."""
        result = self._call_mcp_api("GET", "/resources/tags")
        
        if "error" in result:
            return f"Error getting tags: {result['error']}"
        
        if not isinstance(result, list):
            return "No tags found or unexpected format."

        tags = []
        for tag in result:
            if isinstance(tag, dict):
                value = tag.get('value', '')
                if value:
                    tags.append(value)
            else:
                tags.append(str(tag))
        
        if domain:
            domain_lower = domain.lower()
            filtered = [t for t in tags if domain_lower in t.lower()]
            if filtered:
                return f"🏷️ **Tags containing '{domain}'**: {', '.join(filtered)}"
            else:
                return f"🏷️ **No tags found containing '{domain}'**\n\nAll tags: {', '.join(tags[:20])}"

        themes = {
            'Neuroscience': [t for t in tags if any(k in t.lower() for k in ['neuro', 'brain', 'cortex'])],
            'Machine Learning': [t for t in tags if any(k in t.lower() for k in ['ml', 'learning', 'brain'])],
            'Computer Vision': [t for t in tags if any(k in t.lower() for k in ['visual', 'image', 'vision'])],
            'NLP': [t for t in tags if any(k in t.lower() for k in ['language', 'text', 'nlp'])],
            'General': [t for t in tags if not any(k in t.lower() for k in ['neuro', 'brain', 'ml', 'visual', 'language'])]
        }
        
        formatted = f"🏷️ **Available Research Tags** ({len(tags)} total)\n\n"
        
        for theme, theme_tags in themes.items():
            if theme_tags:
                formatted += f"**{theme}**: {', '.join(theme_tags[:8])}\n"
                if len(theme_tags) > 8:
                    formatted += f"  ... and {len(theme_tags) - 8} more\n"
                formatted += "\n"
        
        return formatted
    
    def get_tools(self) -> List[Tool]:
        """Get simple, reliable tools."""
        return [
            Tool(
                name="search_resources",
                description="Search for any type of research resource (datasets, repositories, notebooks, models). Handles all search queries intelligently. Use this for finding specific resources or browsing by topic.",
                func=self.search_resources
            ),
            Tool(
                name="search_projects", 
                description="Search for research projects. Projects can contain multiple resources and are organized by research goals.",
                func=self.search_projects
            ),
            Tool(
                name="get_available_tags",
                description="Get all available research tags, optionally filtered by domain. Useful for understanding how resources are categorized.",
                func=self.get_available_tags
            )
        ]

def create_research_agent() -> AgentExecutor:
    """Create a simple, robust research agent."""

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        temperature=0.1,
        base_url="http://localhost:11434"
    )

    cybershuttle_tools = CybershuttleLangChainTools()
    tools = cybershuttle_tools.get_tools()

    research_prompt = PromptTemplate.from_template("""
    You are a research assistant for the Cybershuttle platform. You help users find datasets, repositories, notebooks, models, and projects.

    Your approach:
    1. Use search_resources for finding any type of resource, as well as its relevant details - it's intelligent and handles all queries.
    2. Use search_projects for finding research projects specifically and their relevant details. These details also include, what datasets they are using, the URL to their repository, etc.
    3. Use get_available_tags to understand all the available tags which describe resources with keywords.
    4. Be direct and helpful - provide clear, formatted results
    5. If something isn't found, suggest alternative search terms

    Available tools: {tool_names}
    Tool descriptions: {tools}

    Use this format:

    Question: the input question you must answer
    Thought: what I need to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (repeat Thought/Action/Action Input/Observation as needed)
    Thought: I now have the answer
    Final Answer: the complete answer with clear formatting

    Question: {input}
    Thought: {agent_scratchpad}
    """)
    
    agent = create_react_agent(llm, tools, research_prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        callbacks=[ResearchCallbackHandler()],
        max_iterations=6,
        handle_parsing_errors=True
    )
    
    return agent_executor

def main():
    """Main interactive loop."""
    print("🚀 **Cybershuttle LangChain + Qwen3 Research Assistant**")
    print("=" * 60)
    print("Simple, robust research discovery!")
    print("Powered by LangChain + Qwen3 (via Ollama)")
    print()

    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server connected")
        else:
            print("⚠️  Ollama server not responding")
            return
    except requests.RequestException:
        print("❌ Cannot connect to Ollama")
        return

    print("🤖 Initializing Qwen3 research agent...")
    try:
        agent = create_research_agent()
        print("✅ Agent ready!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    print()
    print("**Try these queries:**")
    examples = [
        "Find the SAT-2 classifier repository",
        "Show me neural oscillators dataset", 
        "Find biological RNNs",
        "What neuroscience projects are available?",
        "Show me computer vision repositories",
        "What tags are available for machine learning?"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"   {i}. {example}")
    
    print("\nType 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("🔬 Research Query: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Thank you! 🚀")
                break
            
            if not user_input:
                continue
            
            print(f"\n🧠 **Processing: '{user_input}'**")
            print("-" * 40)

            result = agent.invoke({"input": user_input})
            
            print("\n" + "="*60)
            print("🎯 **Results:**")
            print("="*60)
            print(result['output'])
            print("="*60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting... 🚀")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again.\n")

if __name__ == "__main__":
    try:
        print(f"Using LangChain version: {langchain.__version__}")
    except ImportError:
        print("❌ Install: pip install langchain langchain-ollama")
        exit(1)
    main()