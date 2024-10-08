
from datetime import datetime, time, timezone, timedelta
import os
import pathlib
from typing import List
import uuid
import pytz
import yaml
from shared import app, db
from flask import jsonify, render_template, request, redirect, send_from_directory, url_for
from instagram import post_image

from models import Post

def get_daily_post_times_from_yaml_etc(path):
    with open(path) as f:
        workflow = yaml.safe_load(f)

    est = pytz.timezone('America/New_York')
    utc = pytz.utc

    cron_lines = workflow[True]["schedule"]
    cron_times = [e["cron"] for e in cron_lines]
    post_times_est = []
    for cron_time in cron_times:
        hour = int(cron_time.split(" ")[1])
        minute = int(cron_time.split(" ")[0])
        time_utc = datetime.now(utc).replace(hour=hour, minute=minute, second=0, microsecond=0)
        time_est = time_utc.astimezone(est)
        post_times_est.append(time_est)
    return post_times_est


@app.route('/', methods=['GET'])
def index():
    db.create_all()
    queue_posts = Post.query.filter_by(is_deleted=False, is_posted=False).order_by(Post.position).all()
    stack_posts = Post.query.filter_by(is_deleted=False, is_posted=True).order_by(Post.posted_at.desc()).all()

    for i, post in enumerate(queue_posts):
        if post.position != i + 1:
            post.position = i + 1
    
    db.session.commit()

    yaml_path = pathlib.Path('.github/workflows/post.yml')
    times: List[datetime] = get_daily_post_times_from_yaml_etc(yaml_path)
    daily_post_times_est = ', '.join(['~' + datetime.strftime(time, '%H:%M') for time in times])

    

    instagram_account_url = os.getenv('ISZASC_INSTAGRAM_ACCOUNT_URL')

    return render_template('index.html', queue_posts=queue_posts, stack_posts=stack_posts, daily_post_times_est=daily_post_times_est, instagram_account_url=instagram_account_url)


@app.route('/move/<int:post_id>/<direction>')
def move(post_id, direction):
    post = Post.query.get_or_404(post_id)
    if not post:
        return "Post not found", 404
    if direction == 'up' and post.position > 1:
        post_above = Post.query.filter_by(is_deleted=False, position=post.position - 1).first()
        post_above.position += 1
        post.position -= 1
    elif direction == 'down':
        post_below = Post.query.filter_by(is_deleted=False, position=post.position + 1).first()
        if post_below:
            post_below.position -= 1
            post.position += 1

    db.session.commit()
    return redirect(url_for('index'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if not post:
        return "Post not found", 404
    

    if request.method == 'POST':
        if post.is_posted:
            return "Method not allowed", 405
        secret = os.getenv('ISZASC_EDIT_SECRET')
        user_secret = request.form['secret']
        if user_secret != secret:
            return "Unauthorized", 401
        if 'save' in request.form:
            post.caption = request.form['caption']
            db.session.commit()
            return redirect(url_for('index'))
        elif 'delete' in request.form:
            post.is_deleted = True
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('edit_post.html', post=post)


@app.route('/add', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        files = request.files.getlist('image')  # Get multiple files
        files = [file for file in files if file.filename != '']
        if len(files) > 5:
            return "Maximum 5 images allowed", 400
        
        total_size = sum(len(file.read()) for file in files)
        for file in files:
            file.seek(0)
        if total_size + os.path.getsize(app.config['UPLOAD_FOLDER']) > 1e9:
            return "Maximum 1GB of images allowed", 400

        filenames = []
        for image_file in files:
            filename = str(uuid.uuid4()) + '.jpg'
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)

        caption = request.form['caption']
        max_position = db.session.query(db.func.max(Post.position)).scalar() or 0
        new_post = Post(image_filenames=','.join(filenames), caption=caption, position=max_position + 1, photo_count=len(filenames))
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_post.html')


@app.route('/api/post')
def post():

    user_secret = request.args.get('secret')

    secret = os.getenv('ISZASC_SECRET')

    if user_secret != secret:
        return jsonify({'error': 'Unauthorized'}), 401
    
    is_testing = request.args.get('test') != 'false'

    next_post = Post.query.filter_by(is_deleted=False, is_posted=False).order_by(Post.position).first()
    if not next_post:
        return jsonify({'error': 'No posts found'}), 404
    
    # Get the file paths
    file_paths = next_post.image_filenames.split(',')
    
    # wait the file paths are not full paths
    file_paths = [os.path.join(app.config['UPLOAD_FOLDER'], file_path) for file_path in file_paths]    
    # Post the image
    username = os.getenv('ISZASC_INSTAGRAM_USERNAME')
    password = os.getenv('ISZASC_INSTAGRAM_PASSWORD')
    caption = next_post.caption
    maxtries = os.getenv('NUM_RETRIES')

    media = post_image(username, password, file_paths, caption, int(maxtries), test=is_testing)

    if not media:
        return jsonify({'error': 'Failed to post image'}), 500
    
    utc_now = datetime.now(pytz.utc)

    est_timezone = pytz.timezone('US/Eastern')
    est_now = utc_now.astimezone(est_timezone)

    next_post.is_posted = True
    next_post.posted_at = est_now
    db.session.commit()

    # Return success
    return jsonify({'message': 'Image posted successfully', 
                    'id': next_post.id,
                    'caption': caption,
                    'test': is_testing}), 200

