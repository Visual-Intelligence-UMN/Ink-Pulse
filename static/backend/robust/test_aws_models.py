
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://bedrock-mantle.us-east-2.api.aws/v1",
    api_key=os.getenv("AWS_BEARER_TOKEN_BEDROCK")
)

models = client.models.list()

print("Available models:")
for model in models.data:
    print(model.id)
