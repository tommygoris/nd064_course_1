import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging

number_of_connections = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global number_of_connections
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    number_of_connections += 1
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post


def get_post_count():
    connection = get_db_connection()
    num_post = connection.execute('SELECT COUNT(*) FROM posts',).fetchone()
    connection.close()
    return num_post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(asctime)s, %(message)s')

# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.error('Failed to retrieve the requested article with an id of: ' + str(post_id))
        return render_template('404.html'), 404
    else:
        app.logger.info('Article "' + post[2] + '" retrieved!')
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('The About Us page has been retrieved!')
    return render_template('about.html')


@app.route('/healthz')
def healthz():
    return app.response_class(
        response="result: OK - healthy",
        status=200,
        mimetype='application/json'
    )


@app.route('/metrics')
def metrics():
    global number_of_connections
    num_post = get_post_count()
    num_conns = number_of_connections

    metrics_info = {
        'db_connection_count': num_conns,
        'post_count': num_post[0]
    }

    return app.response_class(
        response=json.dumps(metrics_info),
        status=200,
        mimetype='application/json'
    )


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            app.logger.info('Article "' + title + '" has been created!')

            return redirect(url_for('index'))

    return render_template('create.html')


# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')
