import openai
import requests
import json
import os

# Set your OpenAI API key here or via environment variable
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "<Add your Open AI Key here>")
)

functions = [
    {
        "name": "get_employee",
        "description": "Retrieve employee information by employee ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "integer",
                    "description": "The unique ID of the employee."
                }
            },
            "required": ["employee_id"]
        }
    }
]

def call_mcp(employee_id):
    url = f"http://127.0.0.1:8000/employee/{employee_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Employee {employee_id} not found."}

def main():
    user_message = input("Enter your prompt: ")

    # Step 1: Send the message to OpenAI with the function schema
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",  # or "gpt-4-1106-preview"
        messages=[{"role": "user", "content": user_message}],
        functions=functions,
        function_call="auto"
    )

    message = response.choices[0].message

    # Step 2: Check if the model wants to call a function
    if message.function_call:
        func_call = message.function_call
        print(f"Model wants to call function: {func_call.name} with arguments {func_call.arguments}")
        args = json.loads(func_call.arguments)
        employee_id = args["employee_id"]

        # Step 3: Call your MCP server
        employee_info = call_mcp(employee_id)
        print("Employee info from MCP server:", employee_info)

        # Step 4: Optionally, send the result back to the model for further conversation
        followup = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "user", "content": user_message},
                {
                    "role": "function",
                    "name": "get_employee",
                    "content": json.dumps(employee_info)
                }
            ]
        )
        print("ChatGPT's response with employee info:")
        print(followup.choices[0].message.content)
    else:
        print("Model did not call a function. Response:")
        print(message.content)

if __name__ == "__main__":
    main()