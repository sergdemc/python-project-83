from flask import Flask, render_template, flash, redirect
from flask import url_for, request, g, get_flashed_messages
from psycopg2.extras import NamedTupleCursor
import validators
from dotenv import load_dotenv
import psycopg2
import os
from datetime import datetime
from urllib.parse import urlparse

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
DEBUG = os.getenv('DEBUG')

app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
    conn = psycopg2.connect(app.config['DATABASE_URL'])
    return conn


def create_db():
    db = connect_db()
    with app.open_resource('database.sql', mode='r') as f:
        db.cursor().execute(f.read())
    db.commit()
    db.close()


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


def get_url_errors(url: str) -> list:
    errors = []
    if not url:
        errors.append('URL обязателен')
    if len(url) > 255:
        errors.append('URL превышает 255 символов')
    if not validators.url(url) or (validators.url(url) and errors):
        errors.append('Некорректный URL')
    return errors


def normalize_url(url: str) -> str:
    parsed_url = urlparse(url)
    return parsed_url._replace(
        path='',
        params='',
        query='',
        fragment=''
    ).geturl()


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def get_urls():
    query_db = (
        'SELECT '
        'urls.id AS id, '
        'urls.name AS name, '
        'url_checks.created_at '
        'AS last_check, code_response '
        'FROM urls '
        'LEFT JOIN url_checks '
        'ON urls.id = url_checks.url_id '
        'AND url_checks.id = ('
        'SELECT max(id) FROM url_checks WHERE urls.id = url_checks.url_id) '
        'ORDER BY urls.id DESC;'
    )
    with get_db() as db:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(query_db)
            data = cursor.fetchall()
    db.close()
    return render_template('urls.html', items=data)


@app.post('/urls')
def post_url():
    url = request.form.get('url')
    errors = get_url_errors(url)
    if errors:
        for error in errors:
            flash(error, 'alert-danger')
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'index.html',
            url=url,
            messages=messages
        ), 422

    url = normalize_url(url)
    db = get_db()
    with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
        cursor.execute('SELECT * FROM urls WHERE name=(%s)', (url,))
        current_url = cursor.fetchone()
        if current_url:
            flash('Страница уже существует', 'alert-info')
            url_id = current_url.id
        else:
            cursor.execute('INSERT INTO urls (name, created_at) '
                           'VALUES (%s, %s)',
                           (url, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            cursor.execute('SELECT * FROM urls WHERE name=(%s)', (url,))
            url_id = cursor.fetchone().id
            flash('Страница успешно добавлена', 'alert-success')
    db.close()
    return redirect(url_for('url_info', id=url_id)), 301


@app.get('/urls/<int:id>')
def url_info(id):
    with get_db() as db:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute('SELECT * FROM urls WHERE id=(%s)', (id,))
            url_info = cursor.fetchone()
            cursor.execute('SELECT * '
                           'FROM url_checks '
                           'WHERE url_id=(%s) '
                           'ORDER BY id DESC', (id,))
            url_check = cursor.fetchone()

    db.close()
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'url_info.html',
        url_info=url_info,
        url_check=url_check,
        messages=messages
    )


@app.post('/url/int: <id>/checks')
def url_check(id):
    return redirect(url_for('url_info', id=id))


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


if __name__ == '__main__':
    app.run(debug=True)
