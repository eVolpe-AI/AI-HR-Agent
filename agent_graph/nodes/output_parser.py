from InquirerPy import inquirer


def output_parser(state):
    # print(
    #     "\n================================= OUTPUT PARSER =================================\n"
    # )
    # print(f"{state["messages"][-1].content} \n \n")

    # continue_dialogue = inquirer.select(
    #     message="Czy chcesz kontynuować rozmowę?",
    #     choices=["nie", "kontynuuj"],
    # ).execute()

    # new_state = state.copy()

    # if continue_dialogue == "nie":
    #     state["continue_conversation"] = False
    # else:
    #     next = input("> ")
    #     new_state["continue_conversation"] = True
    #     new_state["messages"].append(
    #         {
    #             "content": f"{next}",
    #             "type": "user",
    #         }
    #     )
    # return new_state
    return state
