from shared import app, db
from server import index, move
from sys import version_info

assert version_info.major == 3 and version_info.minor >= 11, "This app requires Python 3.11+"

def create_database():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_database()
    app.run(host='localhost', port=8010)
