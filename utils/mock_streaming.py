import random
import time


def stream_lorem_ipsum(
    min_total_size=100,
    max_total_size=500,
    min_chunk_size=1,
    max_chunk_size=10,
    min_delay=0.1,
    max_delay=1.0,
):
    """
    Simulates streaming of LLM response in chunks with lorem ipsum text.

    :param total_size: Total size of the text to stream.
    :param min_chunk_size: Minimum size of each chunk in characters.
    :param max_chunk_size: Maximum size of each chunk in characters.
    :param min_delay: Minimum delay between chunks in seconds.
    :param max_delay: Maximum delay between chunks in seconds.
    """
    lorem_ipsum = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. "
        "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    )

    total_size = random.randint(min_total_size, max_total_size)

    text_to_stream = (lorem_ipsum * ((total_size // len(lorem_ipsum)) + 1))[:total_size]

    i = 0
    while i < total_size:
        chunk_size = random.randint(min_chunk_size, max_chunk_size)
        delay = random.uniform(min_delay, max_delay)

        yield text_to_stream[i : i + chunk_size]

        i += chunk_size

        time.sleep(delay)
