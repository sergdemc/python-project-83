from flask import Flask, render_template, flash, redirect, abort,\
    url_for, request, g, get_flashed_messages
from psycopg2.extras import NamedTupleCursor
from urllib.parse import urlparse
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup

import psycopg2
import validators
import os
import requests


load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
DEBUG = os.getenv('DEBUG')

app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
    """Opens DB connection and returns it"""

    conn = psycopg2.connect(app.config['DATABASE_URL'])
    return conn


def create_db():
    """Additional function for creating tables in DB using database.sql file"""

    with app.app_context():
        db = connect_db()
        with app.open_resource('database.sql', mode='r') as sql_file:
            db.cursor().execute(sql_file.read())
        db.commit()
        db.close()


def get_db():
    """Creates DB connection if it hasn't already been made"""

    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


def validate_url(url: str) -> list:
    """Validates url and returns list with url errors if happens"""

    errors = []
    if not url:
        errors.append('URL обязателен')
    if len(url) > 255:
        errors.append('URL превышает 255 символов')
    if not validators.url(url) or (validators.url(url) and errors):
        errors.append('Некорректный URL')
    return errors


def normalize_url(url: str) -> str:
    """Returns normalized URL: https://example.ru"""

    parsed_url = urlparse(url)
    return parsed_url._replace(
        path='',
        params='',
        query='',
        fragment=''
    ).geturl()


def parse_page(page_text: str) -> dict:
    """Getting h1, title and description from page content"""

    checks = {}
    soup = BeautifulSoup(page_text, 'html.parser')
    checks['h1'] = soup.h1.get_text().strip()
    checks['title'] = soup.title.string
    all_metas = soup.find_all('meta')
    for meta in all_metas:
        if meta.get('name') == 'description':
            checks['description'] = meta.get('content')
    return checks


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def get_urls():
    """Shows all added URLs with last check dates and status codes if any"""

    query_db = (
        'SELECT '
        'urls.id AS id, '
        'urls.name AS name, '
        'url_checks.created_at AS last_check, '
        'status_code '
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
    """
    Get new URL, validates the URL.
    Adds the URL to DB if it isn't there and passed validation.
    Redirect to url_info.
    """
    url = request.form.get('url')
    errors = validate_url(url)
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
                           (url, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                           )
            cursor.execute('SELECT * FROM urls WHERE name=(%s)', (url,))
            url_id = cursor.fetchone().id
            flash('Страница успешно добавлена', 'alert-success')
    db.commit()
    db.close()
    return redirect(url_for('url_info', id=url_id)), 301


@app.get('/urls/<int:id>')
def url_info(id):
    """
    Shows URL information and made checks
    :param id: URL's id
    """

    with get_db() as db:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute('SELECT * FROM urls WHERE id=(%s)', (id,))
            url = cursor.fetchone()
            if not url:
                abort(404)

            cursor.execute('SELECT * '
                           'FROM url_checks '
                           'WHERE url_id=(%s) '
                           'ORDER BY id DESC', (id,))
            checks = cursor.fetchall()

    db.close()
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'url_info.html',
        url=url,
        checks=checks,
        messages=messages
    )


@app.post('/url/<int:id>/checks')
def url_checks(id):
    """
    Checks requested URL.
    If no errors, adds got data to DB.
    :param id: URL's id
    :return: redirect to url_info
    """

    with get_db() as db:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute('SELECT * FROM urls WHERE id=(%s)', (id,))
            url = cursor.fetchone()

    try:
        response = requests.get(url.name)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', 'alert-danger')
        return redirect(url_for('url_info', id=id))

    checks = parse_page(response.text)

    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute(
                'INSERT INTO url_checks '
                '(url_id, status_code, h1, title, description, created_at) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (id, response.status_code, checks.get('h1'),
                 checks.get('title'), checks.get('description'),
                 datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            flash('Страница успешно проверена', 'alert-success')
    db.close()

    return redirect(url_for('url_info', id=id))


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


if __name__ == '__main__':
    app.run(debug=True)
