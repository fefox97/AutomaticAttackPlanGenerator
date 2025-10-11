from datetime import datetime
import os
import time
from flask import current_app as app
from flask_socketio import SocketIO
import requests
import json
from apps import celery
from github import Github, Auth
import re
import shutil
from apps.authentication.models import Users

def create_celery_notification(title, message, icon="fa fa-info", buttons=None, user_id=None, date=None):
    from apps.notifications.notify import create_notification
    socketio = SocketIO(message_queue="redis://redis:6379/0")
    data = {
            "title": title,
            "message": message,
            "icon": icon,
            "buttons": buttons,
            "date": date if date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    socketio.emit('receive_notification', data, to=Users.query.get(user_id).notification_session_id)
    create_notification(title=title, message=message, icon=icon, buttons=buttons, user_id=user_id, date=date)

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
def retrieve_wiki_pages(wiki_repo_url=None, wiki_folder=None, wiki_images_folder=None, user_id=None):
    def get_all_md_files(repo, path=""):
        md_files = []
        contents = repo.get_contents(path)
        for content in contents:
            if content.type == "dir":
                md_files.extend(get_all_md_files(repo, content.path))
            elif content.type == "file" and content.path.endswith('.md'):
                md_files.append(content.path)
        return md_files

    def get_image_files(repo, path=""):
        image_files = []
        contents = repo.get_contents(path)
        for content in contents:
            if content.type == "dir":
                image_files.extend(get_image_files(repo, content.path))
            elif content.type == "file" and re.search(r'\.(png|jpg|jpeg|gif|bmp|svg)$', content.path, re.IGNORECASE):
                image_files.append(content.path)
        return image_files

    with app.app_context():
        try:
            if not wiki_repo_url:
                raise Exception("Wiki repository URL is not set in settings")
            auth = Auth.Token(app.config['GITHUB_REPO_TOKEN'])
            g = Github(auth=auth)
            repo = g.get_repo(wiki_repo_url)
            pages = get_all_md_files(repo)
            images = get_image_files(repo)
            app.logger.info(f"Found {images} images in the wiki repository {wiki_repo_url}")

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

            for image in images:
                image_content = repo.get_contents(image)
                image_data = image_content.decoded_content
                dest_path = os.path.join(wiki_images_folder, image.split('/')[-1])
                dest_dir = os.path.dirname(dest_path)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)
                with open(dest_path, 'wb') as img_file:
                    img_file.write(image_data)
            create_celery_notification(title="Wiki retrieved successfully", 
                                message=f"The wiki has been retrieved successfully from the repository {wiki_repo_url}.",
                                icon="fa fa-check",
                                buttons=None,
                                user_id=user_id)
            return pages
        except Exception as e:
            app.logger.error(f"Error retrieving wiki pages: {e}", exc_info=True)

@celery.task
def test_celery(user_id=None):
    with app.app_context():
        try:
            create_celery_notification(title="Test notification", 
                                message="This is a test notification from Celery task",
                                icon="fa fa-info",
                                buttons=None,
                                user_id=user_id)
            return "Celery is working fine!"
        except Exception as e:
            app.logger.error(f"Error in test_celery task: {e}", exc_info=True)
            raise Exception("Error in test_celery task")