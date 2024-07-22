from langchain_core.messages import RemoveMessage


def tool_permit(state):
    tool_to_use = state["messages"][-1].tool_calls[0]["name"]

    print(
        f"""\n================================= Tool Permition Message ================================="""
    )
    print(f"""Agent MintHCM chce wykorzystać: {tool_to_use}""")
    answer = input(
        "Czy zezwolić na użycie narzędzia? (wpisz 'tak' by udzielić zgody): \n> "
    )

    new_state = state.copy()
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
    return new_state
