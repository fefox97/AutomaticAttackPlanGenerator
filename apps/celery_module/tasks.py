import os
import time
from flask import current_app as app
import requests
import json
from apps import celery
from apps.databases.models import Settings
from github import Github, Auth
import re
import shutil

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

@celery.task
def retrieve_wiki_pages(wiki_repo_url=None, wiki_folder=None):
    def get_all_md_files(repo, path=""):
        md_files = []
        contents = repo.get_contents(path)
        for content in contents:
            if content.type == "dir":
                md_files.extend(get_all_md_files(repo, content.path))
            elif content.type == "file" and content.path.endswith('.md'):
                md_files.append(content.path)
        return md_files

    with app.app_context():
        try:
            if not wiki_repo_url:
                raise Exception("Wiki repository URL is not set in settings")
            auth = Auth.Token(app.config['GITHUB_REPO_TOKEN'])
            g = Github(auth=auth)
            repo = g.get_repo(wiki_repo_url)
            pages = get_all_md_files(repo)

            if not os.path.exists(wiki_folder):
                os.makedirs(wiki_folder)
            else:
                # Clear the existing wiki folder
                for file in os.listdir(wiki_folder):
                    file_path = os.path.join(wiki_folder, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)

            app.logger.info(f"Retrieved {len(pages)} pages from the wiki repository {wiki_repo_url}")

            # Ricostruisci la struttura di cartelle e file
            for page in pages:
                file_content = repo.get_contents(page)
                file_content_decoded = file_content.decoded_content.decode('utf-8')
                title_header_pattern = r"---[\s\S]*?title:\s*.+[\s\S]*?---"
                if file_content_decoded not in [None, ''] and re.match(title_header_pattern, file_content_decoded.lstrip(), re.IGNORECASE | re.MULTILINE):
                    dest_path = os.path.join(wiki_folder, page)
                    dest_dir = os.path.dirname(dest_path)
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir, exist_ok=True)
                    with open(dest_path, 'w') as f:
                        f.write(file_content_decoded)
            return pages
        except Exception as e:
            app.logger.error(f"Error retrieving wiki pages: {e}", exc_info=True)