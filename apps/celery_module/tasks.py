from flask import current_app as app
import requests
import json
from apps import celery

@celery.task
def query_llm(prompt):
    with app.app_context():
        app.logger.info(app.config["OPENROUTER_MODEL"])
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {app.config["OPENROUTER_API_KEY"]}",
                    "HTTP-Referer": app.config["URL"],
                    "X-Title": app.config["SITE_NAME"],
                },
                data=json.dumps({
                    "model": app.config["OPENROUTER_MODEL"],
                    "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                    ]
                }),
                timeout=100
            )
            # check if the response has choices
            if 'error' in response.json():
                raise Exception(response.json()['error'])
            response_text = response.json()['choices'][0]['message']['content']
            return response_text
        
        except:
            raise Exception("Error making the request to LLM")
