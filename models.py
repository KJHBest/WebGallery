from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Association table for many-to-many relationship between Image and Tag
image_tags = db.Table('image_tags',
    db.Column('image_id', db.Integer, db.ForeignKey('image.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    tags = db.relationship('Tag', secondary=image_tags, lazy='subquery',
                          backref=db.backref('images', lazy=True))
    likes = db.relationship('Like', backref='image', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'title': self.title,
            'description': self.description,
            'views': self.views,
            'likes_count': len(self.likes),
            'tags': [tag.to_dict() for tag in self.tags],
            'created_at': self.created_at.isoformat()
        }


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint to prevent duplicate likes from same session
    __table_args__ = (db.UniqueConstraint('image_id', 'session_id', name='unique_like'),)
