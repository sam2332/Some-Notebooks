import os
import PySimpleGUI as sg


def setup(gpt_caller):
    @gpt_caller.register_tool
    def read_file(path):
        """This tool reads the content of a file at the given path"""
        if not os.path.exists(path):
            return f"File does not exist at {path}"
        with open(path, "r") as f:
            return f.read()

    @gpt_caller.register_tool
    def copy_file(path, new_path):
        """This tool copies a file from the given path to the new path"""
        with open(path, "r") as f:
            content = f.read()
        with open(new_path, "w") as f:
            f.write(content)
        return f"Copied file from {path} to {new_path}"

    @gpt_caller.register_tool
    def append_file(path, content):
        """This tool appends content to a file at the given path"""
        with open(path, "a") as f:
            f.write(content)
        return f"Appended content to {path}"

    @gpt_caller.register_tool
    def write_file(path, content):
        """This tool writes the content of a file at the given path"""
        if os.path.exists(path):
            confirm = sg.popup_yes_no(
                f"File {path} already exists. Do you want to overwrite it?"
            )
            if confirm == "Yes":
                with open(path, "w") as f:
                    f.write(content)
                return f"Overwrote content of {path}"
            else:
                return "File overwrite cancelled"
        else:
            with open(path, "w") as f:
                f.write(content)
            return f"Wrote content to {path}"

    @gpt_caller.register_tool
    def delete_file(path):
        """This tool deletes a file at the given path"""
        if os.path.exists(path):
            confirm = sg.popup_yes_no(f"Are you sure you want to delete file {path}?")
            if confirm == "Yes":
                os.remove(path)
                return f"Deleted file {path}"
            else:
                return "File deletion cancelled"
        else:
            return f"File does not exist at {path}"
        return f"Appended content to {path}"

    @gpt_caller.register_tool
    def create_dir(path):
        """This tool creates a directory at the given path"""
        if os.path.exists(path):
            return f"Directory already exists at {path}"
        os.mkdir(path)
        return f"Created directory at {path}"

    @gpt_caller.register_tool
    def list_dir(path):
        """This tool lists the files and directories in the given path"""
        return "\n".join(os.listdir(path))
