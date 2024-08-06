def pretty_print_messages(messages: list) -> str:
    for message in messages:
        message_type = message.type
        match message_type:
            case "system":
                print(f"System message: {message.content}")
            case "human":
                print(f"Human message: {message.content}")
            case "ai":
                print(f"AI message: {message.content}")
            case "tool":
                print(f"Tool message: {message.content}")
            case _:
                print(f"Unknown message: {message} of type {message_type}")

        print("---------------------------------------------")
    print("\n\n")
