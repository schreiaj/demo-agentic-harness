import inspect
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from function_schema import get_function_schema
from openrouter import OpenRouter

# This is just for coloring the terminal
from rich import print

load_dotenv()

# This just sets up the LLM API we're going to use
openrouter_api = OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
    server_url=os.getenv("OPENROUTER_BASE_URL", None),
)

model = os.getenv("OPENROUTER_MODEL")


# TODO: Tell the assistant about the tools it has
SYSTEM_PROMPT = """
You are a coding assistant whose goal it is to help us solve coding tasks.
"""

# BEGIN - TOOL Defs


# Just a helper to make paths easier
def to_abs_path(path_str):
    """
    file.py -> /Users/you/project/file.py
    """
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def list_files_tool(path: str) -> Dict[str, Any]:
    """
    Lists the files in a directory
    :param path: The path to a directory to list files from.
    :return: A list of files in the directory.
    """
    full_path = to_abs_path(path)
    all_files = []
    for item in full_path.iterdir():
        all_files.append(
            {"filename": item.name, "type": "file" if item.is_file() else "dir"}
        )
    return {"path": str(full_path), "files": all_files}


def read_file_tool(filename: str) -> Dict[str, Any]:
    """
    Gets the full content of a file
    :param filename: The name of the file to read.
    :return: The full content of the file.
    """
    full_path = to_abs_path(filename)
    with open(str(full_path), "r") as f:
        content = f.read()
    return {"file_path": str(full_path), "content": content}


def edit_file_tool(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """
    Replaces first occurrence of old_str with new_str in file. If old_str is empty,
    create/overwrite file with new_str.
    :param path: The path to the file to edit.
    :param old_str: The string to replace.
    :param new_str: The string to replace with.
    :return: A dictionary with the path to the file and the action taken.
    """
    full_path = to_abs_path(path)
    if old_str == "":
        full_path.write_text(new_str, encoding="utf-8")
        return {"path": str(full_path), "action": "created_file"}
    original = full_path.read_text(encoding="utf-8")
    if original.find(old_str) == -1:
        return {"path": str(full_path), "action": "old_str not found"}
    edited = original.replace(old_str, new_str, 1)
    full_path.write_text(edited, encoding="utf-8")
    return {"path": str(full_path), "action": "edited"}


TOOLS = [list_files_tool, read_file_tool, edit_file_tool]

# We need this to map from name to declared tools
TOOLS_DICT = dict(zip([t.__name__ for t in TOOLS], TOOLS))
# END - TOOL DEFS


# BEGIN - HELPER METHODS
def get_tool_str_representation(tool):
    schema = get_function_schema(tool)
    return {"type": "function", "function": schema}


def get_system_prompt():
    return SYSTEM_PROMPT


def get_tools():
    return [get_tool_str_representation(t) for t in TOOLS]


def wrap_input(str):
    return f"[grey][bold]User:[/bold]{str}[/grey]"


def wrap_llm(str):
    return f"[blue][bold]LLM: [/bold]{str}[/blue]"


def wrap_error(str):
    return f"[red bold]{str}[/red bold]"


# END - HELPER METHODS


def main():
    # We're going to hold our conversation here
    conversation = [{"role": "system", "content": get_system_prompt()}]
    print(f"[bold red]Model:[/bold red] [underline]{model}[/underline]")
    while True:
        try:
            user_input = input("User: ")
        except (KeyboardInterrupt, EOFError):
            break
        conversation.append({"role": "user", "content": user_input.strip()})
        # Now, the problem is, if the llm wants to call multiple tools... what do we do?
        # Simple, we loop until the llm doesn't want to call more tools
        while True:
            response = openrouter_api.chat.send(
                messages=conversation, model=model, tools=get_tools()
            )
            # Let's extract tool calls
            tool_calls = response.choices[0].message.tool_calls
            # In the case of tool calls, let's show we wanted to do them
            if tool_calls:
                for call in tool_calls:
                    function = call.function
                    print(
                        f"[purple]Tool Use Requested: {function.name} with args {function.arguments}[/purple]"
                    )
                    # Now we call the tool
                    try:
                        args = json.loads(function.arguments)
                        resp = TOOLS_DICT[function.name](**args)
                        print(wrap_llm(f"tool_result({json.dumps(resp)})"))
                        conversation.append(
                            {
                                "role": "assistant",
                                "content": f"tool_result({json.dumps(resp)})",
                            }
                        )
                    # Let's at least tell the LLM an error occured
                    except Exception as e:
                        print(wrap_error(e))
                        conversation.append(
                            {
                                "role": "assistant",
                                "content": f"tool_error({json.dumps(e)})",
                            }
                        )

            # Otherwise, let's print response
            else:
                print(wrap_llm(response.choices[0].message.content))
                conversation.append(
                    {
                        "role": "assistant",
                        "content": response.choices[0].message.content,
                    }
                )
                break


if __name__ == "__main__":
    main()
