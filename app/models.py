from flask.ext.bcrypt import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

from app import db, lm
from app.helpers import slugify, utcnow


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    registered = db.Column(db.DateTime, default=utcnow)
    name = db.Column(db.String(64), nullable=False, unique=True)
    password_hash = db.Column(db.String(64))
    posts = db.relationship(
        'Post',
        order_by='Post.published.desc()',
        passive_updates=False,
        cascade='all,delete-orphan',
        backref='author',
    )

    def __init__(self, name, password):
        self.name = name
        self.change_password(password)

    def __repr__(self):
        return u'<User(%s, %s)>' % (self.id, self.name)

    def compare_password(self, password):
        """Compare password against stored password hash."""
        return check_password_hash(self.password_hash, password)

    def change_password(self, password):
        """Change current password to a new password."""
        self.password_hash = generate_password_hash(password, 6)


@lm.user_loader
def load_user(id):
    return User.query.get(id)


class Post(db.Model):
    PER_PAGE = 5

    id = db.Column(db.Integer, primary_key=True)
    published = db.Column(db.DateTime, nullable=False)
    edited = db.Column(db.DateTime, nullable=False)
    title = db.Column(db.String, nullable=False)
    body = db.Column(db.String, nullable=False)
    slug = db.Column(db.String, nullable=False, unique=True)
    author_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False,
    )
    comments = db.relationship(
        "Comment",
        order_by="Comment.posted",
        passive_updates=False,
        cascade="all,delete-orphan",
        backref="post",
    )
    visible = db.Column(db.Boolean, default=False)

    def __init__(self, title, body, author_id, visible):
        self.published = utcnow()
        self.edited = self.published
        self.title = title
        self.body = body
        self.slug = slugify(self.published, title)
        self.author_id = author_id
        self.visible = visible

    def __repr__(self):
        return u'<Post(%s,%s,%s)>' % (self.id, self.slug, self.author.name)

    def edit(self, title, body, visible):
        """Edit post columns."""
        self.edited = utcnow()
        self.title = title
        self.body = body
        self.slug = slugify(self.published, title)
        self.visible = visible

    def change_title(self, title):
        """Change title.

        The post slug will be updated for the new title with the date the post
        was published.

        """
        self.title = title
        self.slug = slugify(self.published, title)

    @property
    def is_edited(self):
        """Validate if this post has been edited since published."""
        return self.edited > self.published


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    posted = db.Column(db.DateTime, default=utcnow)
    name = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String(510), nullable=False)
    ip = db.Column(db.String(45), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    reply_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    replies = db.relationship(
        'Comment',
        passive_updates=False,
        cascade='all,delete-orphan',
    )

    def __init__(self, name, body, ip, post_id, reply_id=None):
        self.name = name
        self.body = body
        self.ip = ip
        self.post_id = post_id
        self.reply_id = reply_id

    def __repr__(self):
        return u'<Comment(%s,%s,%s)>' % (self.id, self.name, self.body)

    @property
    def is_root(self):
        """Validate if this is not a reply to another comment."""
        return self.reply_id is None

    @property
    def has_replies(self):
        """Validate if this comment has any comment replies."""
        return len(self.replies) > 0
