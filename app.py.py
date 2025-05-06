import os
import logging
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from image_processor import process_images

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
ALLOWED_EXTENSIONS = {'bmp'}

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        flash('No files part', 'danger')
        return redirect(request.url)
    
    files = request.files.getlist('files[]')
    
    if not files or files[0].filename == '':
        flash('No selected files', 'danger')
        return redirect(request.url)
    
    # Create a session folder for this batch of uploads
    session_id = str(uuid.uuid4())
    session['processing_id'] = session_id
    
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    results_dir = os.path.join(app.config['RESULTS_FOLDER'], session_id)
    
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    # Save all files
    file_count = 0
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            file_count += 1
    
    if file_count == 0:
        flash('No valid files uploaded. Only BMP files are accepted.', 'warning')
        return redirect(url_for('index'))
    
    # Process the images
    try:
        results = process_images(upload_dir, results_dir)
        session['results'] = results
        return redirect(url_for('show_results'))
    except Exception as e:
        logger.exception("Error processing images")
        flash(f'Error processing images: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/results')
def show_results():
    if 'results' not in session:
        flash('No processing results found. Please upload images first.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('results.html', results=session['results'])

@app.route('/api/status/<session_id>', methods=['GET'])
def get_status(session_id):
    # This would be used for async processing in a more complex app
    # For now, we'll just return a simple response
    if session.get('processing_id') == session_id:
        return jsonify({
            'status': 'complete',
            'message': 'Processing complete'
        })
    return jsonify({
        'status': 'not_found',
        'message': 'Session not found'
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
