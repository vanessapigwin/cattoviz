import config
from flask import Flask, render_template
from flask_talisman import Talisman
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import random

csp = {
    'default-src': [
        '\'self\'',
        '*.googleapis.com',
        '*.gstatic.com'
        ],
    'script-src': '\'self\''
}

app = Flask(__name__)
app.config.from_object(config.Config)
Talisman(
    app, 
    content_security_policy=csp,
    content_security_policy_nonce_in=['script-src']
    )
db = SQLAlchemy(app)


blogtags = db.Table('blogtags',
                db.Column('blog_id', db.Integer, ForeignKey('blogentry.blog_id'), primary_key=True),
                db.Column('tag_id', db.Integer, ForeignKey('tag.id'), primary_key=True),
                )


class BlogEntry(db.Model):
    __tablename__ = 'blogentry'
    blog_id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    title = db.Column(db.String, nullable=False, unique=True)
    subtitle = db.Column(db.String)

    # define relationship with category
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = relationship('Category', back_populates='blogs')

    date_posted = db.Column(db.String, nullable=False)
    read_time = db.Column(db.Integer, nullable=False)
    thumbnail = db.Column(db.String, nullable=False)
    body_text = db.Column(db.Text, nullable=False)

    #define relationship with tags
    tags = relationship('Tag', secondary=blogtags, lazy='subquery', backref=db.backref('blog_pages', lazy=True))


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    cat_name = db.Column(db.String, nullable=False, unique=True)
    # backpopulate blog list based on category
    blogs = relationship('BlogEntry', back_populates='category')


class Tag(db.Model):
    __tablename = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String, nullable=False, unique=True)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error_handler.html'), 404


@app.route('/')
def home():
    # get featured items
    rows = BlogEntry.query.count()
    featured_ids = random.sample([x+1 for x in range(rows)], 2)
    featured_blogs = BlogEntry.query.filter(BlogEntry.blog_id.in_(featured_ids)).all()
    # get remaining items
    remainder_blogs = BlogEntry.query.order_by(BlogEntry.date_posted.desc())\
        .filter(BlogEntry.blog_id.notin_(featured_ids)).limit(5).all()
    return render_template('index.html', blogs=remainder_blogs, featured=featured_blogs)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/blogs/<int:page>', methods=['GET'])
def all_blogs(page=1):
    per_page = 10
    posts = BlogEntry.query.order_by(BlogEntry.date_posted.desc())\
        .paginate(page, per_page=per_page, max_per_page=per_page, error_out=True)
    # get categories
    categories = Category.query.all()
    # get tags
    tags = Tag.query.all()
    return render_template('blog.html', blogs=posts, categories=categories, tags=tags)


@app.route('/category/<category>/<int:page>')
def categories(category, page=1):
    per_page = 4
    category_queried = Category.query.filter_by(cat_name=category).first()
    blogs = BlogEntry.query.order_by(BlogEntry.date_posted.desc())\
        .filter(BlogEntry.category_id.contains(category_queried.id))\
        .paginate(page, per_page=per_page, max_per_page=per_page, error_out=True)
    return render_template('category.html', category=category, blogs=blogs)


@app.route('/blog/<int:selected_id>')
def get_single_post(selected_id):
    rows = BlogEntry.query.count()
    blog = BlogEntry.query.get(selected_id)
    return render_template('single-post.html', blog=blog, total_entries=rows)


@app.route('/tags/<tag>/<int:page>')
def all_with_tag(tag, page=1):
    per_page = 8
    tag_queried = Tag.query.filter_by(tag_name=tag).first()
    blogs = BlogEntry.query.order_by(BlogEntry.date_posted.desc())\
        .filter(BlogEntry.tags.contains(tag_queried))\
        .paginate(page, per_page, error_out=False)
    return render_template('search.html', tag=tag, blogs=blogs)


# @app.route('/applications')
# def applications():
#     return render_template('app-gallery.html')

if __name__ == '__main__':
    app.run(debug=False)