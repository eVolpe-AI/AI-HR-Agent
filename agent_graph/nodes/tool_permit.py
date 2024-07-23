from InquirerPy import inquirer
from langchain_core.messages import RemoveMessage


def tool_permit(state):
    tool_to_use = state["messages"][-1].tool_calls[0]["name"]

    print(
        f"""\n================================= TOOL PERMITION ================================="""
    )
    new_state = state.copy()

    if tool_to_use not in state["safe_tools"]:
        answer = inquirer.select(
            message=f"Agent MintHCM chce wykorzystać: {tool_to_use}. Czy zgadzasz się na użycie tego narzędzia?",
            choices=["tak", "nie"],
        ).execute()

        if answer == "tak":
            new_state["tool_accept"] = 1
        else:
            new_state["tool_accept"] = 0
            new_state["messages"] = [RemoveMessage(id=state["messages"][-1].id)]
            new_state["messages"].append(
                {
                    "content": f"Próbowałeś użyć {tool_to_use} ale użytkownik {state['user']} nie zezwolił na użycie tego narzędzia. Nie próbuj ponownie użyć {tool_to_use}.",
                    "type": "user",
                }
            )

        return new_state
    else:
        new_state["tool_accept"] = 1
        print(
            f"""Narzędzie {tool_to_use} jest bezpieczne i nie wymaga zgody użytkownika."""
        )
        return new_state
