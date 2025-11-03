import os
import uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from models import db, Image, Tag, Like
from sqlalchemy import or_, func

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gallery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Initialize database
db.init_app(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_session_id():
    """Get or create a session ID for tracking likes"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


@app.route('/')
def index():
    """Main gallery page"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    sort_by = request.args.get('sort', 'recent')  # recent, popular, most_liked
    tag_filter = request.args.get('tag', None)

    query = Image.query

    # Apply tag filter
    if tag_filter:
        query = query.join(Image.tags).filter(Tag.name == tag_filter)

    # Apply sorting
    if sort_by == 'popular':
        query = query.order_by(Image.views.desc())
    elif sort_by == 'most_liked':
        query = query.outerjoin(Like).group_by(Image.id).order_by(func.count(Like.id).desc())
    else:  # recent
        query = query.order_by(Image.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    images = pagination.items

    # Get all tags for the filter sidebar
    all_tags = Tag.query.order_by(Tag.name).all()

    return render_template('index.html',
                         images=images,
                         pagination=pagination,
                         all_tags=all_tags,
                         current_tag=tag_filter,
                         sort_by=sort_by)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Image upload page and handler"""
    if request.method == 'POST':
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save file
            file.save(filepath)

            # Create database entry
            title = request.form.get('title', '')
            description = request.form.get('description', '')
            tags_str = request.form.get('tags', '')

            image = Image(
                filename=filename,
                original_filename=original_filename,
                title=title,
                description=description
            )

            # Process tags
            if tags_str:
                tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                for tag_name in tag_names:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    image.tags.append(tag)

            db.session.add(image)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Image uploaded successfully',
                'image_id': image.id
            })

        return jsonify({'error': 'Invalid file type'}), 400

    return render_template('upload.html')


@app.route('/image/<int:image_id>')
def image_detail(image_id):
    """Image detail page"""
    image = Image.query.get_or_404(image_id)

    # Increment view count
    image.views += 1
    db.session.commit()

    # Check if current session has liked this image
    session_id = get_session_id()
    has_liked = Like.query.filter_by(
        image_id=image_id,
        session_id=session_id
    ).first() is not None

    return render_template('detail.html', image=image, has_liked=has_liked)


@app.route('/api/like/<int:image_id>', methods=['POST'])
def like_image(image_id):
    """Toggle like for an image"""
    image = Image.query.get_or_404(image_id)
    session_id = get_session_id()

    # Check if already liked
    existing_like = Like.query.filter_by(
        image_id=image_id,
        session_id=session_id
    ).first()

    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({
            'success': True,
            'liked': False,
            'likes_count': len(image.likes)
        })
    else:
        # Like
        like = Like(image_id=image_id, session_id=session_id)
        db.session.add(like)
        db.session.commit()
        return jsonify({
            'success': True,
            'liked': True,
            'likes_count': len(image.likes)
        })


@app.route('/api/images')
def api_images():
    """API endpoint for getting images with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    tag = request.args.get('tag', None)
    search = request.args.get('search', None)
    sort_by = request.args.get('sort', 'recent')

    query = Image.query

    # Apply filters
    if tag:
        query = query.join(Image.tags).filter(Tag.name == tag)

    if search:
        query = query.filter(
            or_(
                Image.title.ilike(f'%{search}%'),
                Image.description.ilike(f'%{search}%')
            )
        )

    # Apply sorting
    if sort_by == 'popular':
        query = query.order_by(Image.views.desc())
    elif sort_by == 'most_liked':
        query = query.outerjoin(Like).group_by(Image.id).order_by(func.count(Like.id).desc())
    else:
        query = query.order_by(Image.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'images': [img.to_dict() for img in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@app.route('/api/tags')
def api_tags():
    """Get all tags"""
    tags = Tag.query.order_by(Tag.name).all()
    return jsonify({
        'tags': [tag.to_dict() for tag in tags]
    })


@app.route('/api/image/<int:image_id>/delete', methods=['DELETE'])
def delete_image(image_id):
    """Delete an image"""
    image = Image.query.get_or_404(image_id)

    # Delete file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    # Delete from database
    db.session.delete(image)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Image deleted successfully'})


# Create database tables
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
