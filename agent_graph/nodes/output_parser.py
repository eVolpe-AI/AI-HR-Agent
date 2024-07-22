def output_parser(state):
    print("\n-------------------- Output Parser --------------------\n")
    print(state["messages"][-1].content)

    next = input(
        "Czy mogę Ci w czymś jeszcze pomóc? (wpisz 'end' aby zakończyć rozmowę): \n> "
    )

    new_state = state.copy()
    if next == "end":
        new_state["continue_conversation"] = False
    else:
        new_state["continue_conversation"] = True
        new_state["messages"].append(
            {
                "content": f"{next}",
                "type": "user",
            }
        )
    return new_state
