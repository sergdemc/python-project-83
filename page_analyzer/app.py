from flask import Flask, render_template, flash, redirect, abort,\
    url_for, request, get_flashed_messages
from collections import namedtuple
from urllib.parse import urlparse
from dotenv import load_dotenv
from bs4 import BeautifulSoup

import validators
import os
import requests

from page_analyzer.db import get_all_urls, get_url_by_db_field, post_new_url, \
    get_checks_by_url_id, add_url_checks


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
app.config['DEBUG'] = os.getenv('DEBUG')


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
    checks['h1'] = soup.h1.get_text().strip() if soup.h1 else ''
    checks['title'] = soup.title.string if soup.title else ''
    all_metas = soup.find_all('meta')
    for meta in all_metas:
        if meta.get('name') == 'description':
            checks['description'] = meta.get('content', '')
    return checks


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def get_urls():
    """Shows all added URLs with last check dates and status codes if any"""

    urls: namedtuple = get_all_urls()
    return render_template('urls.html', items=urls)


@app.post('/urls')
def post_url():
    """
    Get new URL, validates the URL.
    Adds the URL to DB if it isn't there and passed validation.
    Redirect to url_info.
    """
    url: str = request.form.get('url')
    errors: list = validate_url(url)
    if errors:
        for error in errors:
            flash(error, 'alert-danger')
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'index.html',
            url=url,
            messages=messages
        ), 422

    url: str = normalize_url(url)
    current_url: namedtuple = get_url_by_db_field(url)
    if current_url:
        flash('Страница уже существует', 'alert-info')
        url_id = current_url.id
    else:
        post_new_url(url)
        current_url = get_url_by_db_field(url)
        url_id = current_url.id
        flash('Страница успешно добавлена', 'alert-success')
    return redirect(url_for('url_info', id=url_id)), 301


@app.get('/urls/<int:id>')
def url_info(id):
    """
    Shows URL information and made checks
    :param id: URL's id
    """

    url: namedtuple = get_url_by_db_field(id)
    if not url:
        abort(404)

    checks: namedtuple = get_checks_by_url_id(id)
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

    url: namedtuple = get_url_by_db_field(id)

    try:
        response = requests.get(url.name)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', 'alert-danger')
        return redirect(url_for('url_info', id=id))

    checks: dict = parse_page(response.text)
    checks['url_id'] = id
    checks['status_code'] = response.status_code

    add_url_checks(checks)

    flash('Страница успешно проверена', 'alert-success')

    return redirect(url_for('url_info', id=id))


if __name__ == '__main__':
    app.run()
