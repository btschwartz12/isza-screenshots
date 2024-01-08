
from datetime import datetime
import os
import uuid
import base64
from shared import app, db
from flask import jsonify, render_template, request, redirect, send_from_directory, url_for
from instagram import post_image

from models import Post

@app.route('/icestation', methods=['GET'])
def index():
    queue_posts = Post.query.filter_by(is_posted=False).order_by(Post.position).all()
    stack_posts = Post.query.filter_by(is_posted=True).order_by(Post.posted_at.desc()).all()

    for i, post in enumerate(queue_posts):
        if post.position != i + 1:
            post.position = i + 1
    
    db.session.commit()

    daily_post_time_est = os.getenv('DAILY_POST_TIME_EST')

    return render_template('index.html', queue_posts=queue_posts, stack_posts=stack_posts, daily_post_time_est=daily_post_time_est)


@app.route('/icestation/move/<int:post_id>/<direction>')
def move(post_id, direction):
    post = Post.query.get_or_404(post_id)
    if direction == 'up' and post.position > 1:
        post_above = Post.query.filter_by(position=post.position - 1).first()
        post_above.position += 1
        post.position -= 1
    elif direction == 'down':
        post_below = Post.query.filter_by(position=post.position + 1).first()
        if post_below:
            post_below.position -= 1
            post.position += 1

    db.session.commit()
    return redirect(url_for('index'))


@app.route('/icestation/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/icestation/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        if post.is_posted:
            return "Method not allowed", 405
        if 'save' in request.form:
            post.caption = request.form['caption']
            db.session.commit()
            return redirect(url_for('index'))
        elif 'delete' in request.form:
            db.session.delete(post)
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('edit_post.html', post=post)


@app.route('/icestation/add', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        image_file = request.files['image']
        caption = request.form['caption']
        filename = str(uuid.uuid4()) + '.jpg'

        # Check to make sure the upload folder is not over 100 MB
        total_size = 0
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            total_size += os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], file))
        if total_size > 100000000:
            return "Upload folder is full", 500

        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        max_position = db.session.query(db.func.max(Post.position)).scalar() or 0
        new_post = Post(image_filename=filename, caption=caption, position=max_position + 1)
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_post.html')


@app.route('/icestation/api/getnextpost')
def get_next_post():
    # Return the post and caption for the next post to be posted

    post = Post.query.order_by(Post.position).first()
    if not post:
        return jsonify({'error': 'No posts found'}), 404
    
    # Get the file path
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], post.image_filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'No file found'}), 404
    
    # Read the file and encode it in base64
    with open(file_path, 'rb') as f:
        image_binary = f.read()
    image_base64 = base64.b64encode(image_binary).decode('utf-8')

    # Return the base64 image and caption
    return jsonify({'image': image_base64, 'caption': post.caption}), 200


@app.route('/icestation/api/post')
def post():

    user_secret = request.args.get('secret')

    secret = os.getenv('SECRET')

    if user_secret != secret:
        return jsonify({'error': 'Unauthorized'}), 401
    
    is_testing = request.args.get('test') == 'true'

    next_post = Post.query.filter_by(is_posted=False).order_by(Post.position).first()
    if not next_post:
        return jsonify({'error': 'No posts found'}), 404
    
    # Get the file path
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], next_post.image_filename)

    # Post the image
    username = os.getenv('INSTAGRAM_USERNAME')
    password = os.getenv('INSTAGRAM_PASSWORD')
    caption = next_post.caption
    maxtries = os.getenv('NUM_RETRIES')

    media = post_image(username, password, file_path, caption, int(maxtries), test=is_testing)

    if not media:
        return jsonify({'error': 'Failed to post image'}), 500
    
    next_post.is_posted = True
    next_post.posted_at = datetime.now()
    db.session.commit()

    # Return success
    return jsonify({'message': 'Image posted successfully'}), 200

