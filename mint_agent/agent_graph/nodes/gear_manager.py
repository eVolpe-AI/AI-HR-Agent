from mint_agent.prompts.PromptController import PromptController


def gear_manager(state):
    if state["system_prompt"] is None:
        new_prompt = PromptController.get_simple_prompt()
        return {"system_prompt": new_prompt}
    return state
