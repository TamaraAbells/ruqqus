from werkzeug.contrib.atom import AtomFeed
from datetime import datetime
from ruqqus.classes import *
from ruqqus.helpers.security import *
from ruqqus.helpers.jinja2 import full_link
from flask import *
from ruqqus.__main__ import app, db, limiter

@app.route('/feeds/<sort>')
def feeds(sort=None):
    cutoff = int(time.time()) - (60 * 60 * 24) # 1 day

    posts = db.query(Submission).filter(Submission.created_utc>=cutoff,
                                        Submission.is_banned == False,
                                        Submission.is_deleted == False,
                                        Submission.stickied == False,
                                        Submission.is_public == True)
    sort=sort.lower()

    if sort == "hot":
        posts = posts.order_by(Submission.rank_hot.desc())
    elif sort == "disputed":
        posts = posts.order_by(Submission.score_disputed.desc())
    elif sort == "top":
        posts = posts.order_by(Submission.score.desc())


    feed = AtomFeed(title=f'Top 5 {sort} Posts from ruqqus',
                    feed_url=request.url, url=request.url_root)

    posts = posts.limit(5).all()

    for post in posts:
        feed.add(post.title, post.body_html,
                 content_type='html',
                 author=post.author.username,
                 url=full_link(post.permalink),
                 updated=datetime.fromtimestamp(post.created_utc),
                 published=datetime.fromtimestamp(post.created_utc))
    return feed.get_response()

@app.route('/feeds/@<username>/<key>/<sort>')
def feeds_user(sort=None, username=None, key=None):
    if not username and key:
        return abort(501)

    user = db.query(User).filter_by(username=username).first()
    sort = sort.lower()

    if not validate_hash(key, user.feedkey):
        ##invalid feedkey
        return abort(501)


    posts = user.idlist(sort=sort, t="day")


    feed = AtomFeed(title=f'Top 5 {sort} Posts from ruqqus',
                    feed_url=request.url, url=request.url_root)

    posts = posts.limit(5).all()

    count = 0
    for post in posts:
        if count >=5:
            break

        feed.add(post.title, post.body_html,
                 content_type='html',
                 author=post.author.username,
                 url=full_link(post.permalink),
                 updated=datetime.fromtimestamp(post.created_utc),
                 published=datetime.fromtimestamp(post.created_utc))
        count += 1

    return feed.get_response()