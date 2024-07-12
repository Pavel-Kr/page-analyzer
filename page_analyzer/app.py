from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)
import os
from dotenv import load_dotenv
from page_analyzer import db, utils
from werkzeug.exceptions import NotFound, InternalServerError


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    return render_template(
        'index.html'
    )


@app.get('/urls')
def urls_get():
    conn = db.connect(DATABASE_URL)
    urls = db.get_urls_with_last_checks(conn)
    db.close_connection(conn)
    return render_template(
        'urls.html',
        urls=urls
    )


@app.post('/urls')
def urls_post():
    data = request.form.to_dict()
    if not utils.is_url_valid(data):
        flash('Некорректный URL', 'danger')
        return render_template(
            'index.html',
            url=data['url']
        ), 422

    new_url = utils.get_normalized_url(data['url'])
    conn = db.connect(DATABASE_URL)
    url = db.get_url_by_name(new_url, conn)
    if not url:
        id = db.insert_url(new_url, conn)
        flash('Страница успешно добавлена', 'success')
    else:
        flash('Страница уже существует', 'info')
        id = url.id
    db.close_connection(conn)
    return redirect(url_for('url_get', id=id), 302)


@app.get('/urls/<id>')
def url_get(id):
    conn = db.connect(DATABASE_URL)
    url = db.get_url_by_id(id, conn)
    if not url:
        db.close_connection(conn)
        abort(404)
    url_checks = db.get_checks_by_url_id(id, conn)
    db.close_connection(conn)
    return render_template(
        'show.html',
        url=url,
        checks=url_checks
    )


@app.post('/urls/<id>/checks')
def checks_post(id):
    conn = db.connect(DATABASE_URL)
    url = db.get_url_by_id(id, conn)
    if not url:
        db.close_connection(conn)
        flash('Некорректный URL ID', 'danger')
        return redirect(url_for('urls_get'))
    response = utils.make_request(url)
    if response:
        code, content = response
        h1, title, description = utils.extract_seo_info(content)
        db.insert_url_check(id, code, h1, title,
                            description, conn)
        flash('Страница успешно проверена', 'success')
    else:
        flash('Произошла ошибка при проверке', 'danger')
    db.close_connection(conn)
    return redirect(url_for('url_get', id=id), 302)


@app.errorhandler(NotFound)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(InternalServerError)
def internal_error_handler(e):
    return render_template('500.html'), 500
