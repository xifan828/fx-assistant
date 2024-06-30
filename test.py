import openai

from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the most important factor which affect euro/dollar price?"},
  ],
  temperature=0
)

print(response.choices[0].message.content)