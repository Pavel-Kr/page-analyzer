from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    get_flashed_messages
)
import psycopg2
import os
import requests
from dotenv import load_dotenv
from psycopg2.extras import NamedTupleCursor
from validators.url import url
from urllib.parse import urlparse, urlunparse
from datetime import date
from requests.exceptions import (
    HTTPError,
    Timeout,
    ConnectionError
)


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    return render_template(
        'index.html'
    )


def validate_url(data):
    if not data['url']:
        return False
    return url(data['url'])


@app.get('/urls')
def urls_get():
    messages = get_flashed_messages(with_categories=True)
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute('SELECT id, name FROM urls')
        urls = curs.fetchall()
        entries = []
        for u in urls:
            curs.execute("""SELECT
                            status_code,
                            created_at
                            FROM url_checks
                            WHERE url_id = %s
                            ORDER BY created_at DESC
                            LIMIT 1""", (u.id,))
            check = curs.fetchone()
            entry = {
                'url': u,
                'last_check': check
            }
            entries.append(entry)
        conn.close()
    return render_template(
        'urls.html',
        entries=entries,
        messages=messages
    )


@app.post('/urls')
def urls_post():
    data = request.form.to_dict()
    if not validate_url(data):
        flash('Incorrect URL', 'danger')
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'index.html',
            url=data['url'],
            messages=messages
        ), 422

    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        parsed = urlparse(data['url'])
        normalized = (parsed.scheme, parsed.netloc, '', '', '', '')
        new_url = urlunparse(normalized)
        curs.execute('SELECT * FROM urls WHERE name = %s', (new_url,))
        db_entry = curs.fetchone()
        print(db_entry)
        if not db_entry:
            print('Insert into database')
            curs.execute('INSERT INTO urls (name, created_at) '
                         'VALUES (%s, %s)', (new_url, date.today()))
            conn.commit()
            flash('URL was added successfully', 'success')
        curs.execute('SELECT id FROM urls WHERE name = %s', (new_url,))
        id = curs.fetchone().id
    conn.close()
    return redirect(url_for('url_get', id=id), 302)


@app.get('/urls/<id>')
def url_get(id):
    conn = psycopg2.connect(DATABASE_URL)
    messages = get_flashed_messages(with_categories=True)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute('SELECT * FROM urls WHERE id = %s', (id,))
        url = curs.fetchone()
        if not url:
            return 'Page not found', 404
        curs.execute('SELECT * FROM url_checks WHERE url_id = %s', (id,))
        url_checks = curs.fetchall()
    conn.close()
    return render_template(
        'show.html',
        url=url,
        checks=url_checks,
        messages=messages
    )


@app.post('/urls/<id>/checks')
def checks_post(id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute('SELECT * FROM urls WHERE id = %s', (id,))
        url = curs.fetchone()
        if not url:
            flash('Incorrect URL ID', 'danger')
            conn.close()
            return redirect(url_for('urls_get'))
        try:
            r = requests.get(url.name, timeout=1)
            r.raise_for_status()
            curs.execute('INSERT INTO url_checks'
                         '(url_id, status_code, created_at)'
                         'VALUES (%s, %s, %s)',
                         (id, r.status_code, date.today()))
            conn.commit()
            flash('Page was successfully checked', 'success')
        except (ConnectionError, HTTPError, Timeout):
            flash('An error occured during check', 'danger')
    conn.close()
    return redirect(url_for('url_get', id=id), 302)
