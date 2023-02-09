import os
import sys

from .state import State

class Tool:
    def run_before_recipe_load(self) -> None:
        pass

    def run_after_before_recipe_run(self) -> None:
        pass
    
    def run_after_recipe_run(self) -> None:
        pass

def load_tools(state: State) -> list[Tool]:
    if state.project_config.tools is None:
        return []
    else:
        tools = []
        missing_tools = []
        for tool in state.project_config.tools:
            tool_path = os.path.join(state.env.tool_folder, f"{tool}.py")
            if os.path.isfile(tool_path):
                tools.append(tool)
            else:
                missing_tools.append(tool)
        if len(missing_tools) > 0:
            print(f"Tools {', '.join(missing_tools)} are required by {state.project_config.name} are not installed.")
            print(f"please add them to {state.env.tool_folder}")
            exit(1)
        
        out = []
        missing_create = []
        non_callables = []
        wrong_type = []
        sys.path.append(state.env.tool_folder)
        for tool in tools:
            # load tool path
            sys.path.append(state.env.tool_folder)
            tool_module = __import__(tool)

            # check module includes a function called create
            if not hasattr(tool_module, "create"):
                missing_create.append(tool)
                continue
            create = tool_module.create

            # check type of create function is callable and has type:
            # (env: Environment, global_config: GlobalConfig, project_config: ProjectConfig, action_config: ActionConfig) -> Tool
            if not callable(create):
                non_callables.append(tool)
                continue
            if create.__annotations__ != {
                "state": State,
                "return": Tool
            }:
                wrong_type.append(tool)
                continue
            
            # call create function
            out.append(create(state))
        
        error = False
        if len(missing_create) > 0:
            print(f"Implementation of tools {', '.join(missing_create)} are missing a create function.")
            error = True
        if len(non_callables) > 0:
            print(f"Create function provided by {', '.join(non_callables)} are not callable.")
            error = True
        if len(wrong_type) > 0:
            print(f"Create function provided by {', '.join(wrong_type)} are not of the correct type.")
            error = True

        if error:
            exit(1)
        
        return out
