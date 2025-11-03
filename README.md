# WebGallery - Image Gallery Web Application

A modern, feature-rich image gallery web application built with Flask, inspired by Civitai.com. Upload, view, and organize your images with tags, likes, and view counts.

## Features

- **Image Upload**: Upload images with drag-and-drop support
- **Image Gallery**: Browse images in a responsive grid layout
- **Tags**: Organize images with custom tags
- **Search & Filter**: Filter images by tags and sort by recent, most viewed, or most liked
- **Likes & Views**: Track image popularity with like and view counts
- **Modern UI**: Dark theme inspired by Civitai with smooth animations
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices

## Screenshots

### Gallery View
Browse all images with filtering and sorting options.

### Image Detail
View high-resolution images with tags, likes, and view counts.

### Upload
Easy drag-and-drop image upload with metadata support.

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Custom CSS with CSS Grid and Flexbox

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/KJHBest/WebGallery.git
cd WebGallery
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Uploading Images

1. Click on "Upload" in the navigation bar
2. Drag and drop an image or click to select a file
3. (Optional) Add a title, description, and tags
4. Click "Upload Image"

### Browsing Images

- The main gallery page displays all uploaded images
- Use the sidebar to filter by tags or sort by different criteria
- Click on any image to view it in detail

### Managing Images

- View detailed information on the image detail page
- Like images by clicking the heart icon
- Delete images using the delete button (confirmation required)

### Tags

- Tags are automatically created when uploading images
- Click on any tag to filter images by that tag
- Tags appear in the sidebar for easy filtering

## Project Structure

```
WebGallery/
├── app.py                  # Main Flask application
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── static/
│   ├── css/
│   │   └── style.css     # Stylesheet
│   ├── js/
│   │   └── main.js       # JavaScript
│   └── uploads/          # Uploaded images
├── templates/
│   ├── index.html        # Gallery page
│   ├── upload.html       # Upload page
│   └── detail.html       # Image detail page
└── gallery.db            # SQLite database (created on first run)
```

## Database Schema

### Image
- `id`: Primary key
- `filename`: Unique filename
- `original_filename`: Original upload name
- `title`: Image title (optional)
- `description`: Image description (optional)
- `views`: View count
- `created_at`: Upload timestamp

### Tag
- `id`: Primary key
- `name`: Tag name (unique)

### Like
- `id`: Primary key
- `image_id`: Foreign key to Image
- `session_id`: User session identifier
- `created_at`: Like timestamp

## API Endpoints

### Public Routes
- `GET /` - Main gallery page
- `GET /upload` - Upload page
- `POST /upload` - Handle image upload
- `GET /image/<id>` - Image detail page

### API Routes
- `POST /api/like/<id>` - Toggle like for an image
- `GET /api/images` - Get images with filters (JSON)
- `GET /api/tags` - Get all tags (JSON)
- `DELETE /api/image/<id>/delete` - Delete an image

## Configuration

Edit `app.py` to customize the application:

```python
# Change secret key for production
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Adjust max file size (default: 16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Add/remove allowed file extensions
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
```

## Development

### Running in Development Mode

The application runs in debug mode by default:

```bash
python app.py
```

### Database Migrations

The database is created automatically on the first run. To reset the database:

```bash
rm gallery.db
python app.py
```

## Production Deployment

For production deployment:

1. Change the `SECRET_KEY` in `app.py`
2. Set `debug=False` in the app.run() call
3. Use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

4. Consider using a reverse proxy like Nginx
5. Use a production database like PostgreSQL instead of SQLite

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Inspired by [Civitai.com](https://civitai.com)
- Built with [Flask](https://flask.palletsprojects.com/)
- Icons from inline SVG

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

## Roadmap

Future enhancements planned:
- User authentication and profiles
- Image collections/albums
- Advanced search functionality
- Image editing tools
- Social features (comments, sharing)
- API rate limiting
- Image optimization and thumbnails
- Multiple image upload
- Bulk operations
- Export functionality

---

Made with ❤️ by [KJHBest](https://github.com/KJHBest)
