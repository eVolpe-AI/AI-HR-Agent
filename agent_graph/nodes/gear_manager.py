from prompts.PromptController import PromptController


def gear_manager(state):
    if state["system_prompt"] is None:
        new_prompt = PromptController.get_default_prompt(state["user"])
        return {"system_prompt": new_prompt}
    return state
