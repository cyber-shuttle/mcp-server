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
- Access to Cybershuttle platform (contact dev@airavata.apache.org for access)

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

# Cybershuttle access token (obtained via device flow)
export CS_ACCESS_TOKEN="your-cybershuttle-token"
```

## Authentication

The server uses OAuth2 device flow authentication with the real Cybershuttle platform:

### Get Authentication Token

1. **Run the authentication script**:
```bash
python cybershuttle_auth.py
```

2. **Follow the prompts**:
   - Visit the provided URL
   - Enter the device code
   - Login with your institutional credentials

3. **Export the token**:
```bash
export CS_ACCESS_TOKEN="your-token-from-script"
```

The authentication uses:
- **Auth Server**: `https://auth.cybershuttle.org`
- **API Server**: `https://api.dev.cybershuttle.org:18899`
- **Client ID**: `cybershuttle-agent`

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
# Quick test (MCP server only)
python test_cybershuttle_mcp.py --quick

# Full test suite
python test_cybershuttle_mcp.py
```

Test authentication:
```bash
python cybershuttle_auth.py
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Ensure `CS_ACCESS_TOKEN` is set correctly
   - Check token expiration (tokens expire after ~2 hours)
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
mcp-server/
├── src/
│   ├── cybershuttle_mcp_server.py
│   ├── cybershuttle_auth.py
│   └── __init__.py
├── demos/
│   └── cybershuttle_openai_demo.py
├── tests/
│   └── test_cybershuttle_mcp.py
├── requirements.txt
├── cybershuttle.yml
└── README.md
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