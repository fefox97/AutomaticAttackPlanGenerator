import time
from flask import current_app as app
import requests
import json
from apps import celery
from apps.databases.models import Settings

@celery.task
def query_llm(prompt, max_tries=10, sleep_time=1):
    with app.app_context():
        try:
            for i in range(max_tries):
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {app.config["OPENROUTER_API_KEY"]}",
                        "HTTP-Referer": app.config["URL"],
                        "X-Title": app.config["SITE_NAME"],
                    },
                    data=json.dumps({
                        "model": Settings.query.filter_by(key='pentest_report_ai_model').first().value,
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
                if response_text == "":
                    app.logger.info(f"Empty response from LLM, retrying in {sleep_time} seconds")
                    time.sleep(sleep_time)
                else:
                    return response_text
            raise Exception("Maximum tries reached, no response from LLM")
        
        except:
            raise Exception("Error making the request to LLM")
