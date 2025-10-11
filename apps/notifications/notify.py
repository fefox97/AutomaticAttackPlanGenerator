from datetime import datetime
from apps import socketio, db
from flask import request
from flask import current_app as app
from flask_security import current_user
from apps.authentication.models import Notifications, Users


@socketio.on('connect')
def handle_connect():
    Users.query.filter_by(id=current_user.id).update({'notification_session_id': request.sid})
    db.session.commit()

# Handle disconnects
@socketio.on('disconnect')
def handle_disconnect():
    Users.query.filter_by(id=current_user.id).update({'notification_session_id': None})
    db.session.commit()

def send_notification(title, message, icon="fa fa-info", buttons=None, user_id=None, date=None):
    data = {
        "title": title,
        "message": message,
        "icon": icon,
        "buttons": buttons,
        "date": date if date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    if user_id:
        socketio.emit("receive_notification", data, to=Users.query.get(user_id).notification_session_id)
    else:
        socketio.emit("receive_notification", data)

def create_notification(title, message, icon="fa fa-info", buttons=None, user_id=None, date=None):
    notification = Notifications(
                    title=title,
                    message=message,
                    icon=icon,
                    buttons=buttons,
                    user_id=user_id,
                    created_on=date
                )
    db.session.add(notification)
    db.session.commit()

def create_send_notification(title, message, icon="fa fa-info", buttons=None, user_id=None, date=None):
    app.logger.info(f"Creating and sending notification to user_id={user_id}: {title} - {message}")
    create_notification(title=title, message=message, icon=icon, buttons=buttons, user_id=user_id, date=date)
    send_notification(title=title, message=message, icon=icon, buttons=buttons, user_id=user_id, date=date)