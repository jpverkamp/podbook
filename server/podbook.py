#!/usr/bin/env python3

import feedgen.feed
import flask
import functools
import os
import sys
import uuid
import yaml

DEBUG_MODE = os.environ.get('DEBUG', False)

UUID_NAMESPACE = uuid.UUID(os.environ.get('UUID_NAMESPACE', uuid.uuid4()))

AUTH_USERNAME = os.environ.get('AUTH_USERNAME', False)
AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD', False)
REQUIRE_AUTH = AUTH_USERNAME and AUTH_PASSWORD

if DEBUG_MODE: print('*** RUNNING IN DEBUG MODE ***')
if not REQUIRE_AUTH: print('*** RUNNING WITHOUT AUTHENTICATION ***')

app = flask.Flask(__name__)

def requires_auth(f):
    '''If we set a username and password, require it for this request.'''

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if REQUIRE_AUTH:
            auth = flask.request.authorization
            if not auth or AUTH_USERNAME != auth.username or AUTH_PASSWORD != auth.password:
                return flask.Response('Must authenticate', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

        return f(*args, **kwargs)
    return decorated

def book_to_uuid(book):
    '''Translate a book folder into a deterministic UUID.'''

    return uuid.uuid5(UUID_NAMESPACE, book)

def uuid_to_book(id, cache = {}):
    '''Translate a UUID from above back into a book folder.'''

    if not isinstance(id, uuid.UUID):
        id = uuid.UUID(id)

    if not id in cache:
        cache.clear()
        for book in os.listdir('books'):
            cache[book_to_uuid(book)] = book

    if not id in cache:
        raise Exception('{} does not match any known book'.format(id))

    return cache[id]

@app.route('/')
@requires_auth
def index():
    result = '<ul>'

    for book in sorted(os.listdir('books')):
        config_path = os.path.join('books', book, 'book.yml')
        if not os.path.exists(config_path):
            continue

        with open(config_path, 'r') as fin:
            config = yaml.load(fin)

        result += '<li><a href="feed/{uuid}.xml">{title} by {author}</a></li>'.format(
            uuid = book_to_uuid(book),
            title = config['title'],
            author = config['author']
        )

    result += '</ul>'
    return result

@app.route('/feed/<uuid>.xml')
def get_feed(uuid):
    book = uuid_to_book(uuid)
    config_path = os.path.join('books', book, 'book.yml')

    with open(config_path, 'r') as fin:
        config = yaml.load(fin)

    fg = feedgen.feed.FeedGenerator()
    fg.load_extension('podcast')

    host_url = flask.request.scheme + '://' + flask.request.host

    feed_link = host_url + '/feed/{uuid}.xml'.format(uuid = uuid)

    fg.id = feed_link
    fg.title(config['title'])
    fg.description('{title} by {author}'.format(title = config['title'], author = config['author']))
    fg.author(name = config['author'])
    fg.link(href = feed_link, rel = 'alternate')

    fg.podcast.itunes_category('Arts')

    for file in sorted(os.listdir(os.path.join('books', book))):
        if not file.endswith('.mp3'):
            continue

        name = file.rsplit('.', 1)[0]

        feed_entry_link = host_url + '/media/{book}/{file}'.format(book = book, file = file)
        feed_entry_link = feed_entry_link.replace(' ', '%20')

        fe = fg.add_entry()

        fe.id(feed_entry_link)
        fe.title(name)
        fe.description('{title} by {author} - {chapter}'.format(
            title = config['title'],
            author = config['author'],
            chapter = name,
        ))
        fe.enclosure(feed_entry_link, 0, 'audio/mpeg')

    return fg.rss_str(pretty = True)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug = DEBUG_MODE)
