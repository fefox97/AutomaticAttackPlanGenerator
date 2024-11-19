import flask_admin

class MyModelView(flask_admin.BaseView):
    @flask_admin.expose('/')
    def index(self):
        return self.render('admin/users.html')