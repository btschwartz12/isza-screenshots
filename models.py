from shared import db

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_filenames = db.Column(db.Text, nullable=False)  # Store filenames as a delimited string
    caption = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    photo_count = db.Column(db.Integer, default=0)  # Number of photos
    is_posted = db.Column(db.Boolean, default=False)
    posted_at = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Post {self.id}>'