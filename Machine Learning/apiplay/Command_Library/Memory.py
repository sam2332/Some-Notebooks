import json


class GPTMemory:
    def __init__(self):
        self.memory_file = "memory.json"
        self.load_memory()

    def load_memory(self):
        try:
            with open(self.memory_file, "r") as f:
                self.memory = json.load(f)
        except FileNotFoundError:
            self.memory = {}

    def save_memory(self):
        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f, indent=4)

    def mem_recall(self, key):
        return self.memory.get(key)

    def mem_memorize(self, key, value):
        self.memory[key] = value
        self.save_memory()

    def mem_search(self, search_string):
        out = []
        for m in self.memory:
            if (
                search_string.lower() in m.lower()
                or search_string.lower() in self.memory[m].lower()
            ):
                out.append(m, self.memory[m])
        return "\n".join(out)

    def mem_forget(self, key):
        if key in self.memory:
            del self.memory[key]
            self.save_memory()

    def mem_list(self):
        return "\n".join(self.memory.keys())


def setup(gpt_caller):
    global memory
    memory = GPTMemory()

    @gpt_caller.register_tool
    def mem_list():
        """
        This function lists all keys in memory.
        """
        return memory.mem_list()

    @gpt_caller.register_tool
    def mem_recall(key):
        """
        This function retrieves a value from memory based on the provided key.
        """
        return memory.mem_recall(key)

    @gpt_caller.register_tool
    def mem_memorize(key, value):
        """
        This function stores a value in memory associated with the provided key.
        """
        memory.mem_memorize(key, value)

    @gpt_caller.register_tool
    def mem_search(key):
        """
        This function checks if a key exists in memory.
        """
        return memory.mem_search(key)

    @gpt_caller.register_tool
    def mem_forget(key):
        """
        This function removes a key-value pair from memory.
        """
        memory.mem_forget(key)
