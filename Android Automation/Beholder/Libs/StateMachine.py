import random
from collections import defaultdict
from functools import partial
from pathlib import Path
from copy import copy

class StateMachine:
    def __init__(self, name, startup_db=None, startup_state=None):
        if startup_db is None:
            self.db = defaultdict(lambda: defaultdict(dict))
        else:
            self.db = startup_db
        self.startup_db = copy(startup_db)
        self.file = Path(f"{name}.StateMachine.json")
        self.function_arguments = {}
        self.functions = {}
        if not self.file.exists():
            self.file.write_text(
                json.dumps(
                    {
                        "name": name,
                        "initialState": startup_state,
                        "currentState": None,
                        "rules": {},
                    }
                )
            )
        self.state = json.loads(self.file.read_text())
        self.changeState(self.state["initialState"])

    def changeState(self, new_state_name):
        if new_state_name is not None:
            if new_state_name in self.state["rules"]:
                self.currentState = self.state["rules"][new_state_name]

            else:
                raise Exception(f"No State Named {new_state_name}")

    def setupInitalTo(self, name):
        self.state["initialState"] = name
        self.file.write_text(json.dumps(self.state))
        self.currentState = self.state["rules"][self.state["initialState"]]

    def addState(self, state_name, can_move_directly_to, *args, **kwargs):
        self.state["rules"][state_name] = {
            "name": state_name,
            "to": can_move_directly_to,
        }
        self.function_arguments[state_name] = kwargs
        self.file.write_text(json.dumps(self.state))
        print("State Added:", state_name)

        def inner(func):

            self.functions[state_name] = func  # partial(func,db=self.db)
            # code functionality here
            return func  # partial(func,db=self.db)

        # returning inner function
        return inner

    def resetState(self):
        self.currentState = self.state["rules"][self.state["initialState"]]
        self.state["currentState"] = self.state["initialState"]
        self.db = self.startup_db
        self.file.write_text(json.dumps(self.state))

    def moveState(self, new_state):
        if new_state in self.currentState["to"]:
            self.currentState = self.state["rules"][new_state]
            self.state["currentState"] = new_state
            self.file.write_text(json.dumps(self.state))
        else:
            raise Exception(f"Bad State Move:{new_state}")

    def run(self, maxOperations=100, print_state_change=False):
        self.running = True
        while self.running and maxOperations > 0:
            maxOperations -= 1
            next_state = self._run_once(print_state_change=print_state_change)
            if next_state is None:
                self.running = False
                break

    def _run_once(self, print_state_change=False):
        if self.currentState["name"] in s.functions:
            next_state = self.functions[self.currentState["name"]](db=self.db)
            if print_state_change:
                print(next_state)
            if next_state is not None:
                self.moveState(next_state)
            return next_state
        else:
            raise Exception("Not Callable")