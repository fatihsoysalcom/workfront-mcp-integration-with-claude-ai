"""
Workfront MCP (Model Context Protocol) & Claude Integration Example.

Demonstrates how Claude uses MCP tools to interact with Adobe Workfront
for marketing campaign creation, task management, and automated reporting.
"""

import json
from typing import Dict, Any, List, Optional


# Mock Adobe Workfront REST API Client
class WorkfrontClient:
    def __init__(self):
        self.projects = {
            "PRJ-101": {
                "id": "PRJ-101",
                "name": "Q4 Digital Marketing Campaign",
                "status": "IN_PROGRESS",
                "owner": "Selin Yilmaz",
                "tasks": [
                    {"id": "TSK-01", "name": "Banner Design", "status": "COMPLETE", "assigned_to": "Ahmet K."},
                    {"id": "TSK-02", "name": "Copywriting Review", "status": "IN_PROGRESS", "assigned_to": "Zeynep B."}
                ]
            }
        }

    def list_projects(self) -> List[Dict[str, Any]]:
        return list(self.projects.values())

    def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        return self.projects.get(project_id)

    def create_task(self, project_id: str, task_name: str, assigned_to: str) -> Dict[str, Any]:
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found.")
        
        task_id = f"TSK-0{len(self.projects[project_id]['tasks']) + 1}"
        new_task = {
            "id": task_id,
            "name": task_name,
            "status": "PLANNED",
            "assigned_to": assigned_to
        }
        self.projects[project_id]["tasks"].append(new_task)
        return new_task


# Model Context Protocol (MCP) Server for Workfront
class WorkfrontMCPServer:
    """Exposes Workfront campaign and task capabilities as MCP tools for Claude."""

    def __init__(self, wf_client: WorkfrontClient):
        self.wf_client = wf_client

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns standard MCP tool schemas exposed to Claude AI."""
        return [
            {
                "name": "workfront_list_projects",
                "description": "Lists all active marketing campaign projects in Workfront.",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "workfront_get_project",
                "description": "Retrieves detailed status and tasks for a specific Workfront campaign project.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Workfront Project ID (e.g., PRJ-101)"}
                    },
                    "required": ["project_id"]
                }
            },
            {
                "name": "workfront_create_task",
                "description": "Creates a new task inside a specified Workfront campaign.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Target Workfront Project ID"},
                        "task_name": {"type": "string", "description": "Name or title of the task"},
                        "assigned_to": {"type": "string", "description": "Assignee name"}
                    },
                    "required": ["project_id", "task_name", "assigned_to"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Handles JSON-RPC / MCP tool call invocations from Claude."""
        if tool_name == "workfront_list_projects":
            return {"status": "success", "data": self.wf_client.list_projects()}
        elif tool_name == "workfront_get_project":
            project = self.wf_client.get_project_details(tool_args.get("project_id", ""))
            if not project:
                return {"status": "error", "message": "Project not found"}
            return {"status": "success", "data": project}
        elif tool_name == "workfront_create_task":
            task = self.wf_client.create_task(
                tool_args["project_id"],
                tool_args["task_name"],
                tool_args["assigned_to"]
            )
            return {"status": "success", "data": task}
        else:
            return {"status": "error", "message": f"Unknown MCP tool: {tool_name}"}


# Claude AI Agent Integration Orchestrator
class ClaudeWorkfrontAgent:
    """Simulates Claude processing prompts and invoking Workfront MCP tools."""

    def __init__(self, mcp_server: WorkfrontMCPServer):
        self.mcp = mcp_server

    def process_request(self, user_prompt: str) -> str:
        print(f"\n--- User Prompt: '{user_prompt}' ---")
        
        # Simulating Claude's tool selection decision engine
        prompt_lower = user_prompt.lower()
        if "projeleri" in prompt_lower or "list campaigns" in prompt_lower:
            tool_call = {"name": "workfront_list_projects", "args": {}}
        elif "görev ekle" in prompt_lower or "add task" in prompt_lower:
            tool_call = {
                "name": "workfront_create_task",
                "args": {
                    "project_id": "PRJ-101",
                    "task_name": "Social Media Asset Creation",
                    "assigned_to": "Caner D."
                }
            }
        else:
            tool_call = {"name": "workfront_get_project", "args": {"project_id": "PRJ-101"}}

        print(f"[Claude AI] Executing MCP Tool: {tool_call['name']} with args: {tool_call['args']}")
        mcp_response = self.mcp.execute_tool(tool_call["name"], tool_call["args"])
        print(f"[Workfront MCP Response]: {json.dumps(mcp_response, indent=2, ensure_ascii=False)}")

        return self._generate_response(tool_call["name"], mcp_response)

    def _generate_response(self, tool_name: str, response: Dict[str, Any]) -> str:
        if response["status"] != "success":
            return f"Error: {response.get('message')}"
        
        data = response["data"]
        if tool_name == "workfront_list_projects":
            return f"Found {len(data)} active project in Workfront. Main campaign: '{data[0]['name']}' ({data[0]['status']})."
        elif tool_name == "workfront_create_task":
            return f"Task created! ID: {data['id']} - '{data['name']}' assigned to {data['assigned_to']}."
        else:
            return f"Campaign '{data['name']}' summary: {len(data['tasks'])} tasks logged in Workfront."


def main():
    print("==================================================")
    print(" Workfront MCP & Claude Integration Simulation")
    print("==================================================")

    client = WorkfrontClient()
    mcp_server = WorkfrontMCPServer(client)
    agent = ClaudeWorkfrontAgent(mcp_server)

    # Display exposed MCP tool schemas
    print("\n[MCP Server] Registered Tools for Claude:")
    for tool in mcp_server.get_tool_definitions():
        print(f" - {tool['name']}: {tool['description']}")

    # Run interactive query simulations
    r1 = agent.process_request("Workfront üzerindeki aktif kampanya projelerini listeler misin?")
    print(f"[Claude Final Output]: {r1}")

    r2 = agent.process_request("PRJ-101 projesine 'Social Media Asset Creation' görev ekle")
    print(f"[Claude Final Output]: {r2}")

    r3 = agent.process_request("PRJ-101 kampanya durumunu raporla")
    print(f"[Claude Final Output]: {r3}")


if __name__ == "__main__":
    main()
