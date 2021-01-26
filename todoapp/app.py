from flask import (
        Flask,
        render_template,
        request,
        redirect,
        url_for, jsonify,
        abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/todoapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    todos = db.relationship('Todo',
                            backref='list',
                            lazy=True,
                            cascade="all, delete-orphan")

    def __repr__(self):
        return f'<TodoList ID: {self.id}, name: {self.name}, todos: {self.todos}>'


class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    todolist_id = db.Column(db.Integer,
                            db.ForeignKey('todolists.id'),
                            nullable=False)

    def __repr__(self):
        return f'<Todo ID: {self.id}, description: {self.description}, complete: {self.completed}>'

# db.create_all()


@app.route('/todos/create', methods=['POST'])
def create_todo():
    error = False
    body = {}
    print('Inside /todos/create')
    try:
        description = request.get_json()['description']
        list_id = request.get_json()['todolist_id']
        print("list_id: ", list_id)
        todo = Todo(description=description,
                    completed=False,
                    todolist_id=list_id)
        db.session.add(todo)
        db.session.commit()
        body['id'] = todo.id
        body['description'] = todo.description
        body['complete'] = todo.completed
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify(body)


@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
def set_completed(todo_id):
    error = False
    try:
        completed = request.get_json()['completed']
        todo = Todo.query.get(todo_id)
        print("Todo: {} completed: {}".format(todo, completed))
        todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return '', 200


@app.route('/todos/<todo_id>/delete', methods=['DELETE'])
def delete_todo(todo_id):
    error = False
    try:
        Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify({'success': True})


@app.route('/lists/create', methods=['POST'])
def create_lists():
    error = False
    body = {}
    print('Inside /lists/create')
    try:
        name = request.get_json()['name']
        list = TodoList(name=name)
        db.session.add(list)
        db.session.commit()
        body['name'] = list.name
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
    else:
        return jsonify(body)


@app.route('/lists/<list_id>/delete', methods=['DELETE'])
def delete_list(list_id):
    error = False
    try:
        list = TodoList.query.get(list_id)
        print("TodoList to be deleted: {}".format(list))
        for todo in list.todos:
            db.session.delete(todo)
        db.session.delete(list)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify({'success': True})


@app.route('/lists/<list_id>/set-completed', methods=['POST'])
def set_list_completed(list_id):
    error = False
    try:
        completed = request.get_json()['completed']
        list = TodoList.query.get(list_id)
        print("/lists/set-completed")
        print("Todo List: {} completed: {}".format(list, completed))
        if completed:
            for todo in list.todos:
                print("marking all todos complete")
                todo.completed = completed
        list.completed = completed
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return '', 200


@app.route('/lists/<list_id>')
def get_list_todos(list_id):
    return render_template('index.html',
        lists=TodoList.query.all(),
        active_list=TodoList.query.get(list_id),
        todos=Todo.query.filter_by(todolist_id=list_id).order_by('id').all())


@app.route('/')
def index():
    return redirect(url_for('get_list_todos', list_id=1))

if __name__ == '__main__':
    app.run(debug=True)
