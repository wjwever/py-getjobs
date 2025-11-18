# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI
import requests

print(os.environ.get("RUYUN_API_KEY"))

def chat():
    client = OpenAI(
        api_key=os.environ.get('RUYUN_API_KEY'),
        base_url="https://api.ruyun.fun/v1")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
        ],
        stream=False
    )

    print(response.choices[0].message.content)

# query all moels
# curl --location -g --request GET "https://api.ruyun.fun/v1/models" --header 'Authorization: Bearer sk-pkTuaNzgy8Ihxdj2SmdpDknci0AqyX4PU06fHIAJf7uuM6RU'
BASE_URL = "https://api.ruyun.fun"
API_KEY = os.environ.get("RUYUN_API_KEY")
def models():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Authorization': f'Bearer {API_KEY}'
    }
    response = requests.get(BASE_URL + "/v1/models", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("JSON数据:", data)
    else:
        print(response)

if __name__ == "__main__":
    models()
