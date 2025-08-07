import pandas as pd
import os
from werkzeug.utils import secure_filename
from src.models.unified_models import Product, Category, db
from flask import current_app

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    """Check if file extension is allowed for bulk upload"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_bulk_upload(file, upload_folder):
    """
    Process bulk product upload from Excel/CSV file
    
    Expected columns: Name, Price, Category, Stock
    Optional columns: Description, Brand
    
    Returns:
        dict: Results with success count, errors, and details
    """
    if not file or file.filename == '':
        return {'success': False, 'error': 'No file provided'}
    
    if not allowed_file(file.filename):
        return {'success': False, 'error': 'File type not allowed. Please use CSV, XLSX, or XLS files.'}
    
    # Save uploaded file temporarily
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    
    try:
        file.save(filepath)
        
        # Read file based on extension
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        if file_ext == 'csv':
            df = pd.read_csv(filepath)
        elif file_ext in ['xlsx', 'xls']:
            df = pd.read_excel(filepath)
        else:
            return {'success': False, 'error': 'Unsupported file format'}
        
        # Validate required columns
        required_columns = ['Name', 'Price', 'Category', 'Stock']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'success': False, 
                'error': f'Missing required columns: {", ".join(missing_columns)}. Required: Name, Price, Category, Stock'
            }
        
        # Process each row
        results = {
            'success': True,
            'total_rows': len(df),
            'successful_imports': 0,
            'errors': [],
            'imported_products': []
        }
        
        for index, row in df.iterrows():
            try:
                # Extract data from row
                name = str(row['Name']).strip()
                price = float(row['Price'])
                category_name = str(row['Category']).strip()
                stock = int(row['Stock'])
                
                # Optional fields
                description = str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else ''
                brand = str(row.get('Brand', '')).strip() if pd.notna(row.get('Brand')) else ''
                
                # Validate data
                if not name or name == 'nan':
                    results['errors'].append(f'Row {index + 2}: Product name is required')
                    continue
                
                if price <= 0:
                    results['errors'].append(f'Row {index + 2}: Price must be greater than 0')
                    continue
                
                if stock < 0:
                    results['errors'].append(f'Row {index + 2}: Stock cannot be negative')
                    continue
                
                # Find or create category
                category = Category.query.filter_by(name=category_name).first()
                if not category:
                    # Create new category
                    category = Category(
                        name=category_name,
                        description=f'Auto-created category for {category_name}',
                        is_active=True
                    )
                    db.session.add(category)
                    db.session.flush()  # Get the ID
                
                # Check if product already exists
                existing_product = Product.query.filter_by(name=name).first()
                if existing_product:
                    results['errors'].append(f'Row {index + 2}: Product "{name}" already exists')
                    continue
                
                # Create new product
                product = Product(
                    name=name,
                    description=description,
                    price=price,
                    stock_quantity=stock,
                    category_id=category.id,
                    brand=brand,
                    is_active=True,
                    is_featured=False
                )
                
                db.session.add(product)
                results['successful_imports'] += 1
                results['imported_products'].append({
                    'name': name,
                    'price': price,
                    'category': category_name,
                    'stock': stock
                })
                
            except ValueError as e:
                results['errors'].append(f'Row {index + 2}: Invalid data format - {str(e)}')
            except Exception as e:
                results['errors'].append(f'Row {index + 2}: Error processing row - {str(e)}')
        
        # Commit all changes
        if results['successful_imports'] > 0:
            db.session.commit()
        else:
            db.session.rollback()
        
        return results
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': f'Error processing file: {str(e)}'}
    
    finally:
        # Clean up temporary file
        if os.path.exists(filepath):
            os.remove(filepath)

def generate_sample_csv():
    """Generate a sample CSV template for bulk upload"""
    sample_data = {
        'Name': [
            'Sample Cigarette Pack',
            'Premium Cigar Box',
            'Rolling Paper Set'
        ],
        'Price': [15.99, 45.00, 3.50],
        'Category': ['Cigarettes', 'Cigars', 'Rolling Papers'],
        'Stock': [100, 25, 200],
        'Description': [
            'High-quality cigarette pack with smooth taste',
            'Premium handcrafted cigars from Cuba',
            'Natural hemp rolling papers'
        ],
        'Brand': ['Marlboro', 'Cohiba', 'RAW']
    }
    
    df = pd.DataFrame(sample_data)
    return df

def validate_bulk_upload_data(df):
    """Validate the structure and data of bulk upload DataFrame"""
    errors = []
    
    # Check required columns
    required_columns = ['Name', 'Price', 'Category', 'Stock']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        errors.append(f'Missing required columns: {", ".join(missing_columns)}')
        return errors
    
    # Validate data types and values
    for index, row in df.iterrows():
        row_num = index + 2  # Account for header row
        
        # Check name
        if pd.isna(row['Name']) or str(row['Name']).strip() == '':
            errors.append(f'Row {row_num}: Product name is required')
        
        # Check price
        try:
            price = float(row['Price'])
            if price <= 0:
                errors.append(f'Row {row_num}: Price must be greater than 0')
        except (ValueError, TypeError):
            errors.append(f'Row {row_num}: Price must be a valid number')
        
        # Check stock
        try:
            stock = int(row['Stock'])
            if stock < 0:
                errors.append(f'Row {row_num}: Stock cannot be negative')
        except (ValueError, TypeError):
            errors.append(f'Row {row_num}: Stock must be a valid integer')
        
        # Check category
        if pd.isna(row['Category']) or str(row['Category']).strip() == '':
            errors.append(f'Row {row_num}: Category is required')
    
    return errors

