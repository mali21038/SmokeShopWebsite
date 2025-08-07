from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app as app
from flask_login import login_required, current_user
from src.models.unified_models import db, Product, Category, Order, OrderItem, User, CartItem
from src.utils.auth import admin_required
from src.utils.file_upload import save_uploaded_file
from src.utils.bulk_upload_simple import process_bulk_upload, validate_csv_headers
import os
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    # Get statistics
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(is_admin=False).count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Revenue calculation
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    
    # Low stock products
    low_stock_products = Product.query.filter(Product.stock_quantity <= 10).all()
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_customers=total_customers,
                         recent_orders=recent_orders,
                         total_revenue=total_revenue,
                         low_stock_products=low_stock_products,
                         page_title='Admin Dashboard - MokTrading')

@admin_bp.route('/products')
@admin_required
def products():
    """Admin products management page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    per_page = 20
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.contains(search))
    
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    
    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    categories = Category.query.all()
    
    return render_template('admin/products.html',
                         products=products,
                         categories=categories,
                         search=search,
                         category_filter=category_filter,
                         page_title='Product Management - MokTrading')

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Add new product"""
    categories = Category.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price', type=float)
        stock_quantity = request.form.get('stock_quantity', type=int)
        category_id = request.form.get('category_id', type=int)
        brand = request.form.get('brand', '')
        is_featured = request.form.get('is_featured') == 'on'
        
        # Validation
        if not name or not price or stock_quantity is None:
            flash('Name, price, and stock quantity are required', 'error')
            return redirect(url_for('admin.add_product'))
        
        if price <= 0:
            flash('Price must be greater than 0', 'error')
            return redirect(url_for('admin.add_product'))
        
        if stock_quantity < 0:
            flash('Stock quantity cannot be negative', 'error')
            return redirect(url_for('admin.add_product'))
        
        # Create product
        product = Product(
            name=name,
            description=description,
            price=price,
            stock_quantity=stock_quantity,
            category_id=category_id if category_id else None,
            brand=brand,
            is_featured=is_featured,
            is_active=True
        )
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                try:
                    from flask import current_app
                    upload_folder = current_app.config['UPLOAD_FOLDER']
                    filename = save_uploaded_file(file, upload_folder)
                    if filename:
                        product.image_filename = filename
                        product.image_url = f'/static/uploads/{filename}'
                except ValueError as e:
                    flash(str(e), 'error')
                except Exception as e:
                    flash(f'Error uploading image: {str(e)}', 'error')
        
        try:
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin.products'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding product', 'error')
    
    return render_template('admin/add_product.html',
                         categories=categories,
                         page_title='Add Product - MokTrading')

@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit existing product"""
    product = Product.query.get_or_404(product_id)
    categories = Category.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price', type=float)
        stock_quantity = request.form.get('stock_quantity', type=int)
        category_id = request.form.get('category_id', type=int)
        brand = request.form.get('brand', '')
        is_featured = request.form.get('is_featured') == 'on'
        is_active = request.form.get('is_active') == 'on'
        
        # Validation
        if not name or not price or stock_quantity is None:
            flash('Name, price, and stock quantity are required', 'error')
            return redirect(url_for('admin.edit_product', product_id=product_id))
        
        if price <= 0:
            flash('Price must be greater than 0', 'error')
            return redirect(url_for('admin.edit_product', product_id=product_id))
        
        if stock_quantity < 0:
            flash('Stock quantity cannot be negative', 'error')
            return redirect(url_for('admin.edit_product', product_id=product_id))
        
        # Update product
        product.name = name
        product.description = description
        product.price = price
        product.stock_quantity = stock_quantity
        product.category_id = category_id
        product.brand = brand
        product.is_featured = is_featured
        product.is_active = is_active
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                try:
                    from flask import current_app
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                    filename = save_uploaded_file(file, upload_folder)
                    if filename:
                        product.image_filename = filename
                        product.image_url = f'/static/uploads/{filename}'
                    flash('Image uploaded successfully!', 'success')
                except ValueError as e:
                    flash(str(e), 'error')
                except Exception as e:
                    flash(f'Error uploading image: {str(e)}', 'error')
        
        try:
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin.products'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating product', 'error')
    
    return render_template('admin/edit_product.html',
                         product=product,
                         categories=categories,
                         page_title=f'Edit {product.name} - MokTrading')

@admin_bp.route('/products/bulk_upload', methods=['GET', 'POST'])
@admin_required
def bulk_upload():
    """Bulk upload products from Excel/CSV"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin.bulk_upload'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin.bulk_upload'))
        
        if file and file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            try:
                result = process_bulk_upload(file)
                if result['success']:
                    flash(f'Successfully uploaded {result["added"]} products!', 'success')
                    if result['errors']:
                        flash(f'Skipped {len(result["errors"])} rows with errors', 'warning')
                else:
                    flash(f'Upload failed: {result["message"]}', 'error')
            except Exception as e:
                flash('Error processing file', 'error')
        else:
            flash('Please upload an Excel (.xlsx, .xls) or CSV (.csv) file', 'error')
        
        return redirect(url_for('admin.bulk_upload'))
    
    return render_template('admin/bulk_upload.html',
                         page_title='Bulk Upload Products - MokTrading')

@admin_bp.route('/orders')
@admin_required
def orders():
    """Admin orders management page"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    per_page = 20
    
    query = Order.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get order statistics
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    completed_orders = Order.query.filter_by(status='completed').count()
    
    return render_template('admin/orders.html',
                         orders=orders,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         completed_orders=completed_orders,
                         status_filter=status_filter,
                         page_title='Order Management - MokTrading')

@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    """View order details"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html',
                         order=order,
                         page_title=f'Order #{order.id} - MokTrading')

@admin_bp.route('/orders/<int:order_id>/update_status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        order.status = new_status
        
        try:
            db.session.commit()
            flash(f'Order status updated to {new_status}', 'success')
            
            # Send notification to customer and admin
            try:
                from src.utils.notifications import NotificationService
                notification_service = NotificationService()
                notification_service.send_order_status_update(order)
            except Exception as e:
                pass  # Don't fail if notification fails
                
        except Exception as e:
            db.session.rollback()
            flash('Error updating order status', 'error')
    else:
        flash('Invalid status', 'error')
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

@admin_bp.route('/completed-orders')
@admin_required
def completed_orders():
    """Admin completed orders page with filtering options"""
    from datetime import datetime, timedelta
    from sqlalchemy import and_, func
    
    # Get filter parameters
    filter_type = request.args.get('filter', 'all')  # all, today, week, month, custom
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Base query for completed orders
    query = Order.query.filter_by(status='completed')
    
    # Apply date filters
    today = datetime.now().date()
    
    if filter_type == 'today':
        start_datetime = datetime.combine(today, datetime.min.time())
        end_datetime = datetime.combine(today, datetime.max.time())
        query = query.filter(and_(Order.created_at >= start_datetime, Order.created_at <= end_datetime))
        filter_label = f"Today ({today.strftime('%Y-%m-%d')})"
        
    elif filter_type == 'week':
        # Current week (Monday to Sunday)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        start_datetime = datetime.combine(week_start, datetime.min.time())
        end_datetime = datetime.combine(week_end, datetime.max.time())
        query = query.filter(and_(Order.created_at >= start_datetime, Order.created_at <= end_datetime))
        filter_label = f"This Week ({week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')})"
        
    elif filter_type == 'month':
        # Current month
        month_start = today.replace(day=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        month_end = next_month - timedelta(days=1)
        start_datetime = datetime.combine(month_start, datetime.min.time())
        end_datetime = datetime.combine(month_end, datetime.max.time())
        query = query.filter(and_(Order.created_at >= start_datetime, Order.created_at <= end_datetime))
        filter_label = f"This Month ({month_start.strftime('%B %Y')})"
        
    elif filter_type == 'custom' and start_date and end_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            start_datetime = datetime.combine(start_date_obj, datetime.min.time())
            end_datetime = datetime.combine(end_date_obj, datetime.max.time())
            query = query.filter(and_(Order.created_at >= start_datetime, Order.created_at <= end_datetime))
            filter_label = f"Custom ({start_date} to {end_date})"
        except ValueError:
            filter_label = "All Completed Orders"
    else:
        filter_label = "All Completed Orders"
    
    # Get paginated orders
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Calculate totals for the filtered period
    filtered_orders = query.all()
    total_orders = len(filtered_orders)
    total_revenue = sum(order.total_amount for order in filtered_orders)
    cash_total = sum(order.total_amount for order in filtered_orders if order.payment_method == 'cash')
    credit_total = sum(order.total_amount for order in filtered_orders if order.payment_method in ['card', 'credit'])
    check_total = sum(order.total_amount for order in filtered_orders if order.payment_method == 'check')
    next_time_total = sum(order.total_amount for order in filtered_orders if order.payment_method == 'next_time')
    
    # Payment method breakdown
    payment_breakdown = {
        'cash': cash_total,
        'credit': credit_total,
        'check': check_total,
        'next_time': next_time_total
    }
    
    # Calculate average order value
    avg_order_value = total_revenue / max(total_orders, 1)
    
    return render_template('admin/completed_orders.html',
                         orders=orders,
                         filter_type=filter_type,
                         filter_label=filter_label,
                         start_date=start_date,
                         end_date=end_date,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         payment_breakdown=payment_breakdown,
                         avg_order_value=avg_order_value,
                         page_title='Completed Orders - MokTrading')

@admin_bp.route('/customers')
@admin_required
def customers():
    """Admin customer management page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = 20
    
    query = User.query.filter_by(is_admin=False)
    
    if search:
        query = query.filter(
            (User.first_name.contains(search)) |
            (User.last_name.contains(search)) |
            (User.email.contains(search)) |
            (User.username.contains(search))
        )
    
    customers = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/customers.html',
                         customers=customers,
                         search=search,
                         page_title='Customer Management - MokTrading')

@admin_bp.route('/categories')
@admin_required
def categories():
    """Admin categories management page"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html',
                         categories=categories,
                         page_title='Category Management - MokTrading')

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def add_category():
    """Add new category"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('Category name is required', 'error')
            return redirect(url_for('admin.add_category'))
        
        # Check if category already exists
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash('Category with this name already exists', 'error')
            return redirect(url_for('admin.add_category'))
        
        category = Category(
            name=name,
            description=description,
            is_active=True
        )
        
        try:
            db.session.add(category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding category', 'error')
    
    return render_template('admin/add_category.html',
                         page_title='Add Category - MokTrading')

@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    """Edit existing category"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        is_active = request.form.get('is_active') == 'on'
        
        if not name:
            flash('Category name is required', 'error')
            return redirect(url_for('admin.edit_category', category_id=category_id))
        
        # Check if category name already exists (excluding current category)
        existing = Category.query.filter(Category.name == name, Category.id != category_id).first()
        if existing:
            flash('Category with this name already exists', 'error')
            return redirect(url_for('admin.edit_category', category_id=category_id))
        
        category.name = name
        category.description = description
        category.is_active = is_active
        
        try:
            db.session.commit()
            flash('Category updated successfully!', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating category', 'error')
    
    return render_template('admin/edit_category.html',
                         category=category,
                         page_title=f'Edit {category.name} - MokTrading')

@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    """Delete category"""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has products
    if category.products:
        flash('Cannot delete category with products. Move products to another category first.', 'error')
        return redirect(url_for('admin.categories'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting category', 'error')
    
    return redirect(url_for('admin.categories'))

@admin_bp.route('/financial_dashboard')
@admin_required
def financial_dashboard():
    """Admin financial dashboard"""
    from datetime import datetime, timedelta
    
    # Calculate financial metrics
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Weekly totals
    weekly_orders = Order.query.filter(Order.created_at >= week_start).all()
    
    cash_total = sum(order.total_amount for order in weekly_orders if order.payment_method == 'cash')
    credit_total = sum(order.total_amount for order in weekly_orders if order.payment_method in ['credit', 'card'])
    unpaid_total = sum(order.total_amount for order in weekly_orders if order.payment_status != 'paid')
    
    return render_template('admin/financial_dashboard.html',
                         cash_payments=cash_total,
                         credit_payments=credit_total,
                         unpaid_amount=unpaid_total,
                         monthly_revenue=cash_total + credit_total,
                         weekly_orders=weekly_orders,
                         week_start=week_start,
                         week_end=week_end,
                         page_title='Financial Dashboard - MokTrading')


@admin_bp.route('/products/bulk_upload/download_template')
@admin_required
def download_template():
    """Download CSV template for bulk upload"""
    import io
    import csv
    from flask import make_response
    
    # Create CSV template
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['name', 'description', 'price', 'stock_quantity', 'category', 'brand'])
    
    # Write example rows
    writer.writerow(['Example Product 1', 'Product description here', '19.99', '100', 'Cigarettes', 'Marlboro'])
    writer.writerow(['Example Product 2', 'Another product description', '25.50', '50', 'Cigars', 'Cuban'])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=product_template.csv'
    
    return response

