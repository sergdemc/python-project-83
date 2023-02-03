from collections import namedtuple
from typing import Union
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv
from psycopg2 import connect
from datetime import datetime
import os


load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')


def get_all_urls():
    """Returns all added URLs with its last check dates and status codes"""

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
    with connect(DATABASE_URL) as db:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(query_db)
            urls = cursor.fetchall()
    db.close()
    return urls


def get_url_by_db_field(arg: Union[str, int]) -> namedtuple:
    """Returns URL by its id or name field"""

    db_field = 'id'
    if isinstance(arg, str):
        db_field = 'name'
    with connect(DATABASE_URL) as db:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(f'SELECT * FROM urls WHERE {db_field}=(%s)', (arg,))
            current_url = cursor.fetchone()
    db.close()
    return current_url


def post_new_url(url: str):
    """Adds new URL to DB"""

    with connect(DATABASE_URL) as db:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute('INSERT INTO urls (name, created_at) '
                           'VALUES (%s, %s)',
                           (url, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                           )

    db.close()


def get_checks_by_url_id(id: int) -> namedtuple:
    """Returns URL checks by URL's id"""

    with connect(DATABASE_URL) as db:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute('SELECT * '
                           'FROM url_checks '
                           'WHERE url_id=(%s) '
                           'ORDER BY id DESC', (id,))
            checks = cursor.fetchall()
    db.close()
    return checks


def add_url_checks(checks: dict):
    """Adds URL's checks to DB"""

    with connect(DATABASE_URL) as db:
        with db.cursor() as cursor:
            cursor.execute(
                'INSERT INTO url_checks '
                '(url_id, status_code, h1, title, description, created_at) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (checks.get('url_id'),
                 checks.get('status_code'),
                 checks.get('h1', ''),
                 checks.get('title', ''),
                 checks.get('description', ''),
                 datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
    db.close()
