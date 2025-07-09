from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

# Define the Employee schema
class Employee(BaseModel):
    id: int
    name: str
    department: str
    title: str
    email: str

# In-memory database
db: Dict[int, Employee] = {
    1: Employee(id=1, name="Alice Smith", department="Engineering", title="Software Engineer", email="alice.smith@example.com"),
    2: Employee(id=2, name="Bob Johnson", department="Marketing", title="Marketing Manager", email="bob.johnson@example.com"),
}

# Tool: Get employee by ID
@app.get("/employee/{employee_id}", response_model=Employee)
def get_employee(employee_id: int):
    employee = db.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

# Tool registry endpoint (for LLMs/agents to discover tools)
@app.get("/tools")
def list_tools():
    return {
        "tools": [
            {
                "name": "get_employee",
                "description": "Retrieve employee information by employee ID.",
                "endpoint": "/employee/{employee_id}",
                "method": "GET",
                "parameters": {
                    "employee_id": "integer"
                },
                "response": Employee.schema()
            }
        ]
    }

# To run: uvicorn filename:app --reload