from shared import db

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    is_posted = db.Column(db.Boolean, default=False)
    posted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Post {self.id}>'