import os
from langgraph.prebuilt import create_react_agent


def get_cur_dir():
    return os.path.dirname(os.path.abspath(__file__))


def get_file_list():
    return os.listdir(get_cur_dir())


def create_folder(folder_name):
    path = os.path.join(get_cur_dir(), folder_name)
    os.makedirs(path, exist_ok=True)
    return f"Folder '{folder_name}' created at {path}"


def move_file(file_name, dest_folder):
    src_path = os.path.join(get_cur_dir(), file_name)
    dest_path = os.path.join(get_cur_dir(), dest_folder, file_name)
    if os.path.exists(src_path) and os.path.exists(os.path.dirname(dest_path)):
        os.rename(src_path, dest_path)
        return f"File '{file_name}' moved to '{dest_folder}'"
    else:
        return f"Error: Source file or destination folder does not exist."


def read_file(file_name):
    path = os.path.join(get_cur_dir(), file_name)
    if os.path.exists(path):
        with open(path, "r") as file:
            return file.read()
    else:
        return f"Error: File '{file_name}' does not exist."


agent = create_react_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    tools=[get_cur_dir, get_file_list, create_folder, move_file, read_file],
    prompt="You are a helpful assistant for me organizing my files",
)

# Run the agent
agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "what files are in the current directory?"}
        ]
    },
    {"config": {"recursion_limit": 250}},
)
