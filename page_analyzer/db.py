import psycopg2
from psycopg2.extras import NamedTupleCursor
from datetime import date


def get_urls_with_last_checks(db_url):
    results = []
    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('SELECT id, name FROM urls')
            urls = curs.fetchall()
            for url in urls:
                curs.execute("""SELECT
                                status_code,
                                created_at
                                FROM url_checks
                                WHERE url_id = %s
                                ORDER BY created_at DESC
                                LIMIT 1""", (url.id,))
                last_check = curs.fetchone()
                res = {
                    'id': url.id,
                    'name': url.name
                }
                if last_check:
                    res['status_code'] = last_check.status_code
                    res['created_at'] = last_check.created_at
                results.append(res)
    return results


def get_url_by_id(id, db_url):
    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('SELECT * FROM urls WHERE id = %s', (id,))
            url = curs.fetchone()
            return url


def get_url_by_name(name, db_url):
    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('SELECT * FROM urls WHERE name = %s', (name,))
            url = curs.fetchone()
            return url


def get_checks_by_url_id(url_id, db_url):
    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('SELECT * FROM url_checks '
                         'WHERE url_id = %s', (url_id,))
            url_checks = curs.fetchall()
            return url_checks


def insert_url(name, db_url):
    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('INSERT INTO urls (name, created_at) '
                         'VALUES (%s, %s)', (name, date.today()))
            conn.commit()


def insert_url_check(url_id, status_code, h1, title, desc, db_url):
    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('INSERT INTO url_checks'
                         '(url_id, status_code, h1, title,'
                         'description, created_at)'
                         'VALUES (%s, %s, %s, %s, %s, %s)',
                         (url_id, status_code, h1, title,
                          desc, date.today()))
            conn.commit()
