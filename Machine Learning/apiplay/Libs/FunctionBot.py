import dotenv


import sys
import os
import openai


import json
import inspect


def safe_json_parse(json_str):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Handle the specific JSON parsing error
        # print(json_str)
        return json_str


# gpt-3.5-turbo-1106
# gpt-4-1106-preview
class GPTtoolCaller:
    def __init__(self, model_name="gpt-4-1106-preview", system_msg=None):
        dotenv.load_dotenv()
        openai.api_key = os.environ["OPENAI_KEY"]
        self.model_name = model_name
        self.tools = {}
        self.system_msg = system_msg
        self.tool_definitions = []
        self.reset()

    def reset(self):
        self.messages = []
        if not self.system_msg is None:
            self.messages.append({"role": "system", "content": self.system_msg})

    def register_tool(self, func):
        self.tools[func.__name__] = func
        params = inspect.signature(func).parameters
        param_info = {
            "type": "object",
            "properties": {},
            "required": list(params.keys()),
        }
        for param in params.values():
            # Example of how to fill the parameter details
            # You might need to adjust this depending on your specific needs
            param_info["properties"][param.name] = {
                "type": "string",  # or other type based on your tool
                "description": param.name,  # or a more detailed description
            }
        self.tool_definitions.append(
            {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": func.__doc__,
                    "parameters": param_info,
                },
            }
        )
        return func

    def query(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        # First GPT-4 call to potentially trigger a tool call

        stopped = False
        while not stopped:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=self.messages,
                tools=self.tool_definitions,
                tool_choice="auto",
            )

            # print(response['choices'])
            for choice in response["choices"]:
                # print(choice)
                message = choice.get("message")
                self.messages.append(message)
                tool_calls = message.get("tool_calls")
                if tool_calls:
                    for tool_call in tool_calls:
                        function_call = tool_call.get("function")
                        tool_name = function_call["name"]
                        arguments_json = function_call["arguments"]
                        # Use the safe JSON parsing method
                        parsed_arguments = safe_json_parse(arguments_json)

                        if "error" in parsed_arguments:
                            return parsed_arguments["error"]
                        elif tool_name in self.tools:
                            # Call the registered tool with the parsed arguments
                            tool_response = "NO REPONSE"
                            try:
                                tool_response = self.tools[tool_name](
                                    **parsed_arguments
                                )
                                if tool_response is None or tool_response == "":
                                    tool_response = "NO REPONSE"
                            except Exception as e:
                                tool_response = "Error: " + str(e)

                            print("||-> ", tool_name, arguments_json)
                            self.messages.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": tool_name,
                                    "content": tool_response,
                                }
                            )
                if choice["finish_reason"] == "stop":
                    print("==")
                    self.messages.append(choice["message"])
                    print(choice["message"]["content"])
                    stopped = True
