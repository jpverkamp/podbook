#!/usr/bin/env python3

import feedgen.feed
import flask
import os
import sys
import yaml

DEBUG_MODE = '--debug' in sys.argv or os.environ.get('DEBUG', False)

app = flask.Flask(__name__)

@app.route('/')
def index():
    result = '<ul>'

    for path in sorted(os.listdir('books')):
        config_path = os.path.join('books', path, 'book.yml')
        print(config_path)

        if not os.path.exists(config_path):
            continue

        with open(config_path, 'r') as fin:
            config = yaml.load(fin)

        result += '<li><a href="feed/{path}.xml">{title} by {author}</a></li>'.format(
            path = path,
            title = config['title'],
            author = config['author']
        )

    result += '</ul>'
    return result

@app.route('/feed/<feed>.xml')
def get_feed(feed):
    config_path = os.path.join('books', feed, 'book.yml')

    with open(config_path, 'r') as fin:
        config = yaml.load(fin)

    fg = feedgen.feed.FeedGenerator()
    fg.load_extension('podcast')

    host_url = flask.request.scheme + '://' + flask.request.host

    feed_link = host_url + '/feed/{feed}.xml'.format(feed = feed)

    fg.id = feed_link
    fg.title(config['title'])
    fg.description('{title} by {author}'.format(title = config['title'], author = config['author']))
    fg.author(name = config['author'])
    fg.link(href = feed_link, rel = 'alternate')

    fg.podcast.itunes_category('Arts')

    for file in sorted(os.listdir(os.path.join('books', feed))):
        if not file.endswith('.mp3'):
            continue

        name = file.rsplit('.', 1)[0]

        feed_entry_link = host_url + '/feed/{feed}/{file}'.format(feed = feed, file = file)
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
