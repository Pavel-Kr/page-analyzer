from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
import os
import requests
from dotenv import load_dotenv
from requests.exceptions import (
    HTTPError,
    Timeout,
    ConnectionError
)
from bs4 import BeautifulSoup
from .utils import (
    is_url_valid,
    get_normalized_url,
    extract_seo_info
)
from page_analyzer import db


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
    urls = db.get_urls_with_last_checks(DATABASE_URL)
    return render_template(
        'urls.html',
        urls=urls
    )


@app.post('/urls')
def urls_post():
    data = request.form.to_dict()
    if not is_url_valid(data):
        flash('Некорректный URL', 'danger')
        return render_template(
            'index.html',
            url=data['url']
        ), 422

    new_url = get_normalized_url(data['url'])
    db_entry = db.get_url_by_name(new_url, DATABASE_URL)
    if not db_entry:
        db.insert_url(new_url, DATABASE_URL)
        flash('Страница успешно добавлена', 'success')
        id = db.get_url_by_name(new_url, DATABASE_URL).id
    else:
        flash('Страница уже существует', 'info')
        id = db_entry.id
    return redirect(url_for('url_get', id=id), 302)


@app.get('/urls/<id>')
def url_get(id):
    url = db.get_url_by_id(id, DATABASE_URL)
    if not url:
        return 'Page not found', 404
    url_checks = db.get_checks_by_url_id(id, DATABASE_URL)
    return render_template(
        'show.html',
        url=url,
        checks=url_checks
    )


@app.post('/urls/<id>/checks')
def checks_post(id):
    url = db.get_url_by_id(id, DATABASE_URL)
    if not url:
        flash('Некорректный URL ID', 'danger')
        return redirect(url_for('urls_get'))
    try:
        r = requests.get(url.name, timeout=1)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
        h1, title, description = extract_seo_info(soup)
        db.insert_url_check(id, r.status_code, h1, title,
                            description, DATABASE_URL)
        flash('Страница успешно проверена', 'success')
    except (ConnectionError, HTTPError, Timeout):
        flash('Произошла ошибка при проверке', 'danger')
    return redirect(url_for('url_get', id=id), 302)
