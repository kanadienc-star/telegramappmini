from flask import Flask, request
import requests
import os
from keep_alive import keep_alive

keep_alive()

from flask import Flask, request, jsonify

app = Flask(__name__)

DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get('message', '')
        response = requests.post(
            "https://api.deepinfra.com/v1/openai/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/Meta-Llama-3-8B-Instruct",
                "messages": [{"role": "user", "content": user_input}]
            }
        )
        response_json = response.json()
        answer = response_json['choices'][0]['message']['content']
        return jsonify({'reply': answer})
    except Exception as e:
        return jsonify({'reply': f'Произошла ошибка: {str(e)}'})
