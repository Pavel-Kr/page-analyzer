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
from dotenv import load_dotenv
from psycopg2.extras import NamedTupleCursor
from validators.url import url
from urllib.parse import urlparse, urlunparse
from datetime import date


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
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute("""SELECT
                        urls.id AS id,
                        urls.name AS name,
                        MAX(url_checks.created_at) AS created_at,
                        url_checks.status_code AS status_code
                        FROM urls LEFT JOIN url_checks
                        ON urls.id = url_checks.url_id
                        GROUP BY urls.id, urls.name, url_checks.status_code""")
        urls = curs.fetchall()
        return render_template(
            'urls.html',
            urls=urls
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
        return redirect(url_for('url_get', id=id), 302)


@app.get('/urls/<id>')
def url_get(id):
    messages = get_flashed_messages(with_categories=True)
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute('SELECT * FROM urls WHERE id = %s', (id,))
        url = curs.fetchone()
        if not url:
            return 'Page not found', 404
        curs.execute('SELECT * FROM url_checks WHERE url_id = %s', (id,))
        url_checks = curs.fetchall()
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
        curs.execute('INSERT INTO url_checks (url_id, created_at)'
                     'VALUES (%s, %s)', (id, date.today()))
        conn.commit()
        flash('Page was successfully checked', 'success')
        return redirect(url_for('url_get', id=id), 302)
