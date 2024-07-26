# async def return_message():
#     yield "THIS IS A STREAMED MESSAGE"


def stream_output(state):
    additional_message = "THIS IS A STREAMED MESSAGE"
    return state, additional_message
