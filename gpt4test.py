# import requests
# import json
# import openai

# openai_api = "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"

# url = 'https://api.openai.com/v1/completions'
# headers = {'content-type': 'application/json', "Authorization":f'Bearer {openai_api}'}

# character1 = "an anxious elven artificer woman, who always wears full plate armor"
# character2 = "a recovering alcoholic changeling who desperately wants to be a good person, but never seems to get it right"
# description = f"**First character**: `{character1}`\n**Second character**: `{character2}`"
# prompt = f"Give a brief idea for a low-stakes encounter, a roleplay scene between two D&D characters in the city of Silverymoon, in Faerûn. The first character is {character1}, and the second character is {character2}. Avoid creating backstory for these characters, as they are pre-existing. The characters have not interacted before this scene. Describe the inciting incident only, and not what happens next."

# payload = {"model":"gpt-4","prompt":prompt,"temperature":0.8,"max_tokens":150}
# payload = json.dumps(payload, indent = 4)
# r = requests.post(url=url, data=payload, headers=headers)
# print(r)
# # print(f"{r.json()['choices'][0]['text']}")


import requests
import json

api_key = "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"

url = 'https://api.openai.com/v1/chat/completions'
headers = {'content-type': 'application/json', "Authorization":f'Bearer {api_key}'}
messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Knock knock."},
        {"role": "assistant", "content": "Who's there?"},
        {"role": "user", "content": "Orange."},
    ]
payload = {
    "model":"gpt-3.5-turbo", 
    "messages":messages,
    "temperature":0.8,
    "max_tokens":150
    }
payload = json.dumps(payload, indent = 4)
r = requests.post(url=url, data=payload, headers=headers)
print(r.json()['choices'][0]['message']['content'])
    