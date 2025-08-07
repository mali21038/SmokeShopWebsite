import csv
import io
from flask import flash
from src.models.unified_models import db, Product, Category

def process_bulk_upload(file):
    """
    Process bulk upload CSV file (simplified version without pandas)
    
    Args:
        file: FileStorage object from Flask request
    
    Returns:
        dict: Result with success status and message
    """
    try:
        # Read CSV content
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_input, start=2):  # Start at 2 because row 1 is header
            try:
                # Extract data from row
                name = row.get('name', '').strip()
                description = row.get('description', '').strip()
                price_str = row.get('price', '').strip()
                stock_str = row.get('stock_quantity', '').strip()
                category_name = row.get('category', '').strip()
                brand = row.get('brand', '').strip()
                
                # Validation
                if not name:
                    errors.append(f"Row {row_num}: Product name is required")
                    error_count += 1
                    continue
                
                if not price_str:
                    errors.append(f"Row {row_num}: Price is required")
                    error_count += 1
                    continue
                
                try:
                    price = float(price_str)
                    if price <= 0:
                        errors.append(f"Row {row_num}: Price must be greater than 0")
                        error_count += 1
                        continue
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid price format")
                    error_count += 1
                    continue
                
                try:
                    stock_quantity = int(stock_str) if stock_str else 0
                    if stock_quantity < 0:
                        errors.append(f"Row {row_num}: Stock quantity cannot be negative")
                        error_count += 1
                        continue
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid stock quantity format")
                    error_count += 1
                    continue
                
                # Find or create category
                category_id = None
                if category_name:
                    category = Category.query.filter_by(name=category_name).first()
                    if not category:
                        # Create new category
                        category = Category(
                            name=category_name,
                            description=f"Auto-created category for {category_name}"
                        )
                        db.session.add(category)
                        db.session.flush()  # Get the ID
                    category_id = category.id
                
                # Check if product already exists
                existing_product = Product.query.filter_by(name=name).first()
                if existing_product:
                    errors.append(f"Row {row_num}: Product '{name}' already exists")
                    error_count += 1
                    continue
                
                # Create new product
                product = Product(
                    name=name,
                    description=description,
                    price=price,
                    stock_quantity=stock_quantity,
                    category_id=category_id,
                    brand=brand,
                    is_active=True,
                    is_featured=False
                )
                
                db.session.add(product)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                error_count += 1
        
        # Commit all changes
        if success_count > 0:
            db.session.commit()
        
        # Prepare result
        result = {
            'success': success_count > 0,
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10],  # Limit to first 10 errors
            'total_errors': len(errors)
        }
        
        return result
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'success_count': 0,
            'error_count': 1,
            'errors': [f"File processing error: {str(e)}"],
            'total_errors': 1
        }

def validate_csv_headers(file):
    """
    Validate CSV file headers
    
    Args:
        file: FileStorage object from Flask request
    
    Returns:
        dict: Validation result
    """
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.reader(stream)
        headers = next(csv_reader, [])
        
        required_headers = ['name', 'price']
        optional_headers = ['description', 'stock_quantity', 'category', 'brand']
        
        missing_required = [h for h in required_headers if h not in headers]
        
        if missing_required:
            return {
                'valid': False,
                'message': f"Missing required columns: {', '.join(missing_required)}"
            }
        
        return {
            'valid': True,
            'message': 'CSV format is valid',
            'headers': headers
        }
        
    except Exception as e:
        return {
            'valid': False,
            'message': f"Error reading CSV file: {str(e)}"
        }

def generate_csv_template():
    """
    Generate CSV template for bulk upload
    
    Returns:
        str: CSV template content
    """
    template_data = [
        ['name', 'description', 'price', 'stock_quantity', 'category', 'brand'],
        ['Example Product 1', 'Product description here', '19.99', '100', 'Cigarettes', 'Marlboro'],
        ['Example Product 2', 'Another product description', '25.50', '50', 'Cigars', 'Cuban'],
        ['Example Product 3', 'Third product example', '15.00', '75', 'Accessories', 'Generic']
    ]
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(template_data)
    
    return output.getvalue()

