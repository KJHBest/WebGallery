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
app.config['READY_FOLDER'] = r'E:\1_WORK\outputs\WebUI'  # Folder for auto-loading images
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


def scan_and_import_ready_images():
    """Scan the ready folder and import new images into the database (no file copying)"""
    ready_folder = app.config['READY_FOLDER']

    # Create folder if it doesn't exist
    os.makedirs(ready_folder, exist_ok=True)

    # Get all existing filenames from database (avoid query in loop)
    existing_filenames = {img.filename for img in Image.query.with_entities(Image.filename).all()}

    # Collect new images to import
    new_images = []
    for filename in os.listdir(ready_folder):
        if not allowed_file(filename):
            continue

        # Check if already imported
        if filename in existing_filenames:
            continue

        # Extract title from filename (without extension)
        title = os.path.splitext(filename)[0]

        # Create database entry (no file copying, use original filename)
        image = Image(
            filename=filename,
            original_filename=filename,
            title=title,
            description=''
        )
        new_images.append(image)

    # Add all new images at once
    if new_images:
        try:
            db.session.add_all(new_images)
            db.session.commit()
            print(f"Imported {len(new_images)} new images from ready folder")
        except Exception as e:
            db.session.rollback()
            print(f"Error importing images: {e}")
            return 0

    return len(new_images)


@app.route('/ready/<path:filename>')
def serve_ready_image(filename):
    """Serve images from ready folder"""
    return send_from_directory(app.config['READY_FOLDER'], filename)


@app.route('/')
def index():
    """Main gallery page"""
    page = request.args.get('page', 1, type=int)
    per_page = 24
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
    per_page = request.args.get('per_page', 21, type=int)
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
    """Delete an image from gallery (removes from DB only, keeps original file)"""
    image = Image.query.get_or_404(image_id)

    # Delete from database only (keep original file in ready folder)
    db.session.delete(image)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Image removed from gallery'})


@app.route('/api/scan', methods=['POST'])
def scan_images():
    """Manually trigger image scan from ready folder"""
    imported = scan_and_import_ready_images()
    return jsonify({
        'success': True,
        'imported': imported,
        'message': f'Imported {imported} new images'
    })


# Create database tables and import initial images
with app.app_context():
    db.create_all()
    # Scan and import images on startup
    print("Scanning for new images...")
    imported = scan_and_import_ready_images()
    if imported > 0:
        print(f"Imported {imported} images on startup")
    else:
        print("No new images to import")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
