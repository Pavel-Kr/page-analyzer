from validators.url import url
from urllib.parse import urlparse, urlunparse


def is_url_valid(data):
    if not data['url']:
        return False
    return url(data['url'])


def get_normalized_url(url):
    parsed = urlparse(url)
    normalized = (parsed.scheme, parsed.netloc, '', '', '', '')
    new_url = urlunparse(normalized)
    return new_url


def extract_seo_info(soup):
    h1 = None
    title = None
    description = None
    if soup.h1:
        h1 = soup.h1.string
    if soup.title:
        title = soup.title.string
    meta = soup.find_all('meta', attrs={'name': 'description'})
    if meta:
        description = meta[0]['content']
    return (h1, title, description)
