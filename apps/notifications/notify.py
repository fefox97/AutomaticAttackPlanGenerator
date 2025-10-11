from datetime import datetime
import json
from apps import socketio, db
from flask import request
from flask import current_app as app
from flask_security import current_user
from apps.authentication.models import Notifications, Users


@socketio.on('connect')
def handle_connect():
    Users.query.filter_by(id=current_user.id).update({'notification_session_id': request.sid})
    db.session.commit()

@socketio.on('disconnect')
def handle_disconnect():
    Users.query.filter_by(notification_session_id=request.sid).update({'notification_session_id': None})
    db.session.commit()

def send_notification(title, message, icon="fa fa-info", links=None, user_id=None, date=None):
    data = {
        "title": title,
        "message": message,
        "icon": icon,
        "buttons": links,
        "date": date if date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    if user_id:
        user_session_id = Users.query.get(user_id).notification_session_id
        if user_session_id:
            socketio.emit("receive_notification", data, to=user_session_id)
    else:
        socketio.emit("receive_notification", data)

def create_notification(title, message, icon="fa fa-info", links=None, user_id=None, date=None):
    notification = Notifications(
                    title=title,
                    message=message,
                    icon=icon,
                    links=json.dumps(links) if links else None,
                    user_id=user_id,
                    created_on=date
                )
    db.session.add(notification)
    db.session.commit()

def create_send_notification(title, message, icon="fa fa-info", links=None, user_id=None, date=None):
    create_notification(title=title, message=message, icon=icon, links=links, user_id=user_id, date=date)
    send_notification(title=title, message=message, icon=icon, links=links, user_id=user_id, date=date)

def create_send_notification_to_admins(title, message, icon="fa fa-info", links=None, date=None):
    admins = Users.query.join(Users.roles).filter_by(name='admin').all()
    for admin in admins:
        create_send_notification(title=title, message=message, icon=icon, links=links, user_id=admin.id, date=date)

def create_send_notification_broadcast(title, message, icon="fa fa-info", links=None, date=None):
    users = Users.query.all()
    for user in users:
        app.logger.info(f"Broadcasting notification to user {user.id} - {user.email}")
        create_send_notification(title=title, message=message, icon=icon, links=links, user_id=user.id, date=date)