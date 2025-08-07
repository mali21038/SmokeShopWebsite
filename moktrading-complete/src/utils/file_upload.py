import os
import uuid
from werkzeug.utils import secure_filename
import secrets

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    """Generate a unique filename while preserving the extension"""
    if not filename:
        return None
    
    # Get file extension
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    # Generate unique filename
    unique_id = str(uuid.uuid4())[:8]
    timestamp = secrets.token_hex(4)
    
    return f"{unique_id}_{timestamp}.{ext}"

def save_uploaded_file(file, upload_folder):
    """
    Save uploaded file (simplified version without PIL)
    
    Args:
        file: FileStorage object from Flask request
        upload_folder: Directory to save the file
    
    Returns:
        str: Filename of saved file or None if failed
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed. Please use PNG, JPG, JPEG, GIF, or WebP.")
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise ValueError("File size too large. Maximum size is 5MB.")
    
    # Generate unique filename
    filename = generate_unique_filename(file.filename)
    if not filename:
        raise ValueError("Invalid filename.")
    
    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_folder, filename)
    
    try:
        file.save(filepath)
        return filename
        
    except Exception as e:
        # Clean up file if it was created
        if os.path.exists(filepath):
            os.remove(filepath)
        raise ValueError(f"Error saving file: {str(e)}")

def save_uploaded_image(file, upload_folder, max_size=(800, 800)):
    """
    Save uploaded image file (simplified version)
    
    Args:
        file: FileStorage object from Flask request
        upload_folder: Directory to save the file
        max_size: Tuple of (width, height) for maximum dimensions (ignored in simple version)
    
    Returns:
        str: Filename of saved image or None if failed
    """
    return save_uploaded_file(file, upload_folder)

def delete_image_file(filename, upload_folder):
    """Delete an image file from the upload folder"""
    if not filename:
        return True
    
    filepath = os.path.join(upload_folder, filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        return True
    except Exception:
        return False

def get_image_url(filename, static_url_prefix='/static/uploads/'):
    """Get the URL for an uploaded image"""
    if not filename:
        return None
    return f"{static_url_prefix}{filename}"

