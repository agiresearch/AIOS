from pathlib import Path
import os

def underline(title: str, character: str = "=") -> str:
    return f"{title}\n{character * len(title)}"


def generate_title(filename: str) -> str:
    # Turn filename into a title
    title = filename.replace("_", " ").title()
    # Handle acronyms and names
    # title = fix_case(title)
    # # Underline title
    title = underline(title)
    return title


def get_root_dir(starting_directory=None):
    if starting_directory is None:
        starting_directory = os.getcwd()

    current_directory = starting_directory

    while True:
        if os.path.isdir(os.path.join(current_directory, '.git')):
            return current_directory

        parent_directory = os.path.dirname(current_directory)

        if parent_directory == current_directory:
            raise FileNotFoundError("No .git directory found in any parent directories")

        current_directory = parent_directory

def generate_tools():
    root_dir = Path(__file__).parent.parent.parent.resolve()

    # Source paths
    script_dir = root_dir / "pyopenagi/tools"
    script_paths = sorted(script_dir.glob("*/*.py"))

    # Destination paths
    doc_dir = root_dir / "docs/source/agent_developer/external_tools"
    doc_paths = [doc_dir / f"{path.stem}.rst" for path in script_paths]

    # Generate the example docs for each example script
    for script_path, doc_path in zip(script_paths, doc_paths):
        script_url = f"https://github.com/agiresearch/AIOS/blob/main/{str(script_path.relative_to(root_dir))}"
        # Make script_path relative to doc_path and call it include_path
        include_path = '../../../..' / script_path.relative_to(root_dir)
        content = (f"{generate_title(doc_path.stem)}\n\n"
                   f"Source code at {script_url}.\n\n"
                   f".. literalinclude:: {include_path}\n"
                   "    :language: python\n"
                   )
        with open(doc_path, "w") as f:
            f.write(content)

    # Generate the toctree for the example scripts
    with open(doc_dir / "tool_index.template.rst") as f:
        examples_index = f.read()
    with open(doc_dir / "tool_index.rst", "w") as f:
        example_docs = "\n   ".join(path.stem for path in script_paths)
        f.write(examples_index.replace(r"%tool_example%", example_docs))
