"""
LangChain Agent API Server

Exposes the LangChain agent as HTTP API for the frontend.
"""

import os
import sys
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from langchain_qwen_demo import create_research_agent, CybershuttleLangChainTools
    from langchain.agents import AgentExecutor
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run this from your mcp-server/demos directory")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

agent_executor: AgentExecutor = None
cybershuttle_tools: CybershuttleLangChainTools = None

def initialize_agent():
    """Initialize your LangChain agent."""
    global agent_executor, cybershuttle_tools
    
    if agent_executor is not None:
        return True
    else:
        try:
            logger.info("🤖 Initializing LangChain + Qwen3 agent...")
            agent_executor = create_research_agent()
            cybershuttle_tools = CybershuttleLangChainTools()
            logger.info("✅ Agent ready!")
            return True
        except Exception as e:
            logger.error(f"❌ Agent init failed: {e}")
            return False

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint matching frontend's expectations."""
    try:
        data = request.json
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        if not agent_executor and not initialize_agent():
            return jsonify({
                "error": "Agent not available. Check Ollama and MCP server.",
                "success": False
            }), 503

        result = agent_executor.invoke({"input": user_message})
        response_text = result.get('output', 'No response generated')

        logger.info(f"✅ Response: {len(response_text)} chars")

        return jsonify({
            "response": response_text,
            "success": True
        })

    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    agent_ready = agent_executor is not None

    ollama_ok = False
    try:
        resp = requests.get("http://localhost:11434/api/version", timeout=3)
        ollama_ok = resp.status_code == 200
    except:
        pass

    mcp_ok = False
    try:
        resp = requests.get("http://localhost:8000/health", timeout=3)
        mcp_ok = resp.status_code == 200
    except:
        pass
    
    return jsonify({
        "status": "healthy" if (agent_ready and ollama_ok) else "degraded",
        "agent_ready": agent_ready,
        "ollama_running": ollama_ok,
        "mcp_server_running": mcp_ok
    })

if __name__ == '__main__':
    print("🚀 LangChain Agent API Server")
    print("=" * 40)

    print("\n🔍 System Check:")
    
    try:
        resp = requests.get("http://localhost:11434/api/version", timeout=3)
        if resp.status_code == 200:
            print("✅ Ollama: Running")
        else:
            print("❌ Ollama: Not responding")
    except:
        print("❌ Ollama: Not accessible")
    
    try:
        resp = requests.get("http://localhost:8000/health", timeout=3)
        if resp.status_code == 200:
            print("✅ MCP Server: Running")
        else:
            print("❌ MCP Server: Not responding")
    except:
        print("❌ MCP Server: Not accessible")

    if initialize_agent():
        print("✅ Agent: Ready")
    else:
        print("❌ Agent: Failed to initialize")
    
    print(f"\n🌐 Starting API server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)