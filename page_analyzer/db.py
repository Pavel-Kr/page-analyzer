import psycopg2
from psycopg2.extras import NamedTupleCursor
from datetime import date
from psycopg2 import sql
from psycopg2.extensions import connection


def connect(db_url):
    return psycopg2.connect(db_url)


def close_connection(conn: connection):
    conn.close()


def get_urls_with_last_checks(conn: connection):
    results = []
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


def get_url_by_key(key, value, conn: connection):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        query = sql.SQL('SELECT * FROM urls WHERE {} = %s').format(
            sql.Identifier(key)
        )
        curs.execute(query, (value,))
        url = curs.fetchone()
        return url


def get_url_by_id(id, conn: connection):
    return get_url_by_key('id', id, conn)


def get_url_by_name(name, conn: connection):
    return get_url_by_key('name', name, conn)


def get_checks_by_url_id(url_id, conn: connection):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute('SELECT * FROM url_checks '
                     'WHERE url_id = %s', (url_id,))
        url_checks = curs.fetchall()
        return url_checks


def insert_url(name, conn: connection):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute('INSERT INTO urls (name, created_at) '
                     'VALUES (%s, %s)', (name, date.today()))
        conn.commit()


def insert_url_check(url_id, status_code, h1, title, desc, conn: connection):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute('INSERT INTO url_checks'
                     '(url_id, status_code, h1, title,'
                     'description, created_at)'
                     'VALUES (%s, %s, %s, %s, %s, %s)',
                     (url_id, status_code, h1, title,
                      desc, date.today()))
        conn.commit()
