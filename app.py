from shared import app, db
from frontend import index, move
from backend import post_insta

def create_database():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_database()
    app.run(debug=True)
