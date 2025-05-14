import time
from flask import current_app as app
import requests
import json
from apps import celery
from apps.databases.models import Settings

@celery.task
def query_llm(app_id, max_tries=10, sleep_time=1):
    with app.app_context():
        try:
            for i in range(max_tries):
                response = requests.post(
                        url=app.config["DIFY_API_URL"],
                        headers={
                            "Authorization": f"Bearer {app.config["DIFY_API_KEY"]}",
                            "Content-Type": "application/json",

                        },
                        data=json.dumps({
                            "inputs": {
                                "app_id": app_id
                            },
                            "response_mode": "blocking",
                            "user": app.config["DIFY_USER"]
                        }),
                        timeout=10000
                    )
                response_status = response.json()['data']['status']
                # check if the response has choices
                if response_status != 'succeeded':
                    raise Exception(f"Error in the response from LLM: {response.json()['data']['error']}")
                response_text = response.json()['data']['outputs']['result']
                if response_text == "":
                    app.logger.info(f"Empty response from LLM, retrying in {sleep_time} seconds")
                    time.sleep(sleep_time)
                else:
                    return response_text
            raise Exception("Maximum tries reached, no response from LLM")
        
        except:
            app.logger.error(f"Error making the request to LLM", exc_info=True)
            raise Exception("Error making the request to LLM")
