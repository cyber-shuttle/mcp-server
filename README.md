# Cybershuttle MCP Server

A Model Context Protocol (MCP) server for Apache Cybershuttle. This server enables AI agents to interact with the Cybershuttle research catalog, allowing natural language queries and operations on datasets, notebooks, models, repositories, projects, and sessions.

## Features

- **Complete Cybershuttle API Integration**: Wraps all major Cybershuttle Research Service endpoints
- **MCP Protocol Support**: Fully compatible with Model Context Protocol for AI agent integration
- **Authentication**: OAuth2 device flow authentication with token management
- **Tool Discovery**: Comprehensive `/tools` endpoint for agent capability discovery
- **OpenAI Integration**: Ready-to-use demo with OpenAI function calling
- **Resource Management**: Create, read, update, and delete operations for all resource types
- **Session Management**: Launch and manage interactive research sessions
- **Project Organization**: Create and manage research projects with multiple resources

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Agent      │    │   MCP Server    │    │   Cybershuttle  │
│   (OpenAI)      │◄──►│                 │◄──►│   API           │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

- **AI Agent**: OpenAI GPT-4 with function calling capabilities
- **MCP Server**: FastAPI-based server that wraps Cybershuttle APIs
- **Cybershuttle API**: Apache Airavata Research Service REST endpoints

## Prerequisites

- Python 3.8+
- OpenAI API key (for the demo)
- Access to Cybershuttle platform (dev instance at https://api.dev.cybershuttle.org:18899)

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd cybershuttle-mcp-server
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
# Required for OpenAI demo
export OPENAI_API_KEY="your-openai-api-key"

# For development/testing (if you have a direct auth token)
export CYBERSHUTTLE_AUTH_TOKEN="your-cybershuttle-token"

# Optional: OAuth2 credentials (for proper device flow)
export CYBERSHUTTLE_CLIENT_ID="your-client-id"
export CYBERSHUTTLE_CLIENT_SECRET="your-client-secret"
```

## Authentication

The server supports two authentication modes:

### 1. Development Mode (Simple Token)
For development and testing, you can use a direct authentication token:

```bash
export CYBERSHUTTLE_AUTH_TOKEN="your-token"
```

### 2. OAuth2 Device Flow (Production)
For production use, implement the full OAuth2 device flow:

```python
from cybershuttle_auth import CybershuttleAuth

auth = CybershuttleAuth()
token = auth.get_access_token()  # This will prompt for device authentication
```

## Usage

### 1. Start the MCP Server

```bash
python cybershuttle_mcp_server.py
```

The server will start on `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

### 2. Test the Server

Check the health endpoint:
```bash
curl http://localhost:8000/health
```

List available tools:
```bash
curl http://localhost:8000/tools
```

### 3. Run the OpenAI Demo

```bash
python cybershuttle_openai_demo.py
```

This will start an interactive chat session where you can ask questions about the Cybershuttle catalog.

## Example Interactions

Here are some example prompts you can try with the AI agent:

### Resource Discovery
- "Show me all datasets in the catalog"
- "Find notebooks related to machine learning"
- "Search for repositories about deep learning"
- "What tags are available in the catalog?"

### Resource Management
- "Create a new dataset for climate research"
- "Add a notebook about data visualization"
- "Import a repository from GitHub"

### Project Management
- "Create a new project for my research"
- "List all my projects"
- "Start a session for project XYZ"

### Session Management
- "Show me all active sessions"
- "Start a new session for my machine learning project"

## API Endpoints

The MCP server provides the following main endpoints:

### Resource Management
- `GET /resources` - List all resources with filtering
- `GET /resources/{id}` - Get specific resource
- `POST /resources/dataset` - Create dataset
- `POST /resources/notebook` - Create notebook
- `POST /resources/repository` - Create repository
- `POST /resources/model` - Create model
- `GET /resources/search` - Search resources
- `GET /resources/tags` - Get all tags

### Project Management
- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /projects/{owner_id}` - Get projects by owner
- `DELETE /projects/{id}` - Delete project

### Session Management
- `GET /sessions` - List sessions
- `GET /hub/start-session/{project_id}` - Start session
- `GET /hub/resume-session/{session_id}` - Resume session
- `PATCH /sessions/{id}` - Update session
- `DELETE /sessions/{id}` - Delete session

### Tool Discovery
- `GET /tools` - List all available tools for agents
- `GET /health` - Health check

## Monitoring and Logging

The server includes comprehensive logging and monitoring:

```python
# Check server health
curl http://localhost:8000/health

# Monitor logs
tail -f logs/cybershuttle_mcp.log
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Test authentication:
```bash
python cybershuttle_auth.py --test
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Ensure `CYBERSHUTTLE_AUTH_TOKEN` is set correctly
   - Check token expiration
   - Verify API endpoint accessibility

2. **OpenAI Integration Issues**:
   - Ensure `OPENAI_API_KEY` is set
   - Check OpenAI account credits
   - Verify function definitions match server endpoints

3. **Connection Issues**:
   - Check if Cybershuttle dev API is accessible
   - Verify network connectivity
   - Check firewall settings

### Debug Mode

Run the server in debug mode:
```bash
python cybershuttle_mcp_server.py --debug
```

## Project Structure

```
cybershuttle-mcp-server/
├── cybershuttle_mcp_server.py      # Main MCP server
├── cybershuttle_openai_demo.py     # OpenAI integration demo
├── cybershuttle_auth.py             # Authentication helper
├── requirements.txt                 # Dependencies
└── README.md                        # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the Apache 2.0 License.

## Acknowledgments

- Apache Airavata team for the Cybershuttle platform
- OpenAI for the function calling capabilities
- Model Context Protocol community