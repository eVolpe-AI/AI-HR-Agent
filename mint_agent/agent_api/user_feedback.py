import os
from typing import Literal

from dotenv import load_dotenv
from langfuse import Langfuse
from pydantic import BaseModel


class Feedback(BaseModel):
    type: str = Literal["positive", "negative"]
    comment: str = None


def send_feedback_to_langfuse(feedback):
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )

    try:
        langfuse.score(
            data_type="CATEGORICAL",
            trace_id="744fb236-95f9-4c87-a832-4f6c6ffa2759",
            name="user_feedback",
            value="positive" if feedback.type == "positive" else "negative",
            comment=feedback.comment,
        )
        print("Feedback sent successfully")
    except Exception as e:
        print(f"Error: {e}")
