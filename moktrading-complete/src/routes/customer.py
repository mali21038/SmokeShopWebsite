from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from src.models.unified_models import db, Product, Category, CartItem, Order, OrderItem
from src.utils.auth import login_required, get_current_user
from decimal import Decimal

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def home():
    """Customer home page"""
    # Get featured products
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
    if not featured_products:
        featured_products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    
    # Get categories
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('customer/home.html', 
                         featured_products=featured_products,
                         categories=categories,
                         page_title='Premium Tobacco Products - MokTrading')

@customer_bp.route('/products')
def products():
    """Product catalog page"""
    category_id = request.args.get('category', type=int)
    sort_by = request.args.get('sort', 'name')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Build query
    query = Product.query.filter_by(is_active=True)
    
    # Filter by category
    if category_id:
        query = query.filter_by(category_id=category_id)
        selected_category = Category.query.get(category_id)
    else:
        selected_category = None
    
    # Search filter
    if search:
        query = query.filter(
            (Product.name.contains(search)) |
            (Product.description.contains(search)) |
            (Product.brand.contains(search))
        )
    
    # Sorting
    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.name.asc())
    
    # Pagination
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('customer/products.html',
                         products=products,
                         selected_category=selected_category,
                         sort_by=sort_by,
                         search=search,
                         page_title='Our Products - MokTrading')

@customer_bp.route('/products/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    product = Product.query.get_or_404(product_id)
    
    if not product.is_active:
        flash('Product not available.', 'error')
        return redirect(url_for('customer.products'))
    
    # Get related products
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    return render_template('customer/product_detail.html',
                         product=product,
                         related_products=related_products,
                         page_title=f'{product.name} - MokTrading')

@customer_bp.route('/cart')
@login_required
def cart():
    """Shopping cart page with tax calculations"""
    from src.utils.tax_calculator import tax_calculator
    
    user = get_current_user()
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    
    # Get user's state for tax calculation (default to Delaware if not set)
    user_state = user.state if user.state else 'DE'
    if len(user_state) > 2:
        # Convert full state name to abbreviation if needed
        state_mapping = {
            'delaware': 'DE', 'california': 'CA', 'new york': 'NY',
            'texas': 'TX', 'florida': 'FL', 'illinois': 'IL'
            # Add more as needed
        }
        user_state = state_mapping.get(user_state.lower(), 'DE')
    
    # Calculate cart total without tax
    cart_subtotal = sum(item.total_price for item in cart_items)
    
    # Calculate taxes if there are items in cart
    tax_summary = None
    if cart_items:
        cart_data = [{'product': item.product, 'quantity': item.quantity} for item in cart_items]
        tax_summary = tax_calculator.calculate_cart_tax(cart_data, user_state)
    
    # For backward compatibility
    cart_total = cart_subtotal
    if tax_summary:
        cart_total = float(tax_summary['grand_total'])
    
    
    # Get recommended products (from different categories)
    recommended_products = []
    if cart_items:
        # Get products from categories not in cart
        cart_categories = [item.product.category_id for item in cart_items]
        recommended_products = Product.query.filter(
            ~Product.category_id.in_(cart_categories),
            Product.is_active == True,
            Product.stock_quantity > 0
        ).limit(3).all()
    
    return render_template('customer/cart.html',
                         cart_items=cart_items,
                         cart_total=cart_total,
                         cart_subtotal=float(cart_subtotal),
                         tax_summary=tax_summary,
                         user_state=user_state,
                         total=cart_total,  # For backward compatibility
                         recommended_products=recommended_products,
                         page_title='Shopping Cart - MokTrading')

@customer_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add item to cart"""
    try:
        user = get_current_user()
        if not user:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Please log in to add items to cart.'})
            flash('Please log in to add items to cart.', 'error')
            return redirect(url_for('auth.login'))
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            product_id = int(data.get('product_id')) if data.get('product_id') else None
            quantity = int(data.get('quantity', 1)) if data.get('quantity') else 1
        else:
            product_id = request.form.get('product_id', type=int)
            quantity = request.form.get('quantity', 1, type=int)
        
        if not product_id or quantity < 1:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Invalid product or quantity.'})
            flash('Invalid product or quantity.', 'error')
            return redirect(request.referrer or url_for('customer.products'))
        
        product = Product.query.get(product_id)
        if not product:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Product not found.'})
            flash('Product not found.', 'error')
            return redirect(request.referrer or url_for('customer.products'))
        
        if not product.is_active:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Product is not available.'})
            flash('Product is not available.', 'error')
            return redirect(request.referrer or url_for('customer.products'))
        
        if not product.is_in_stock:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Product is out of stock.'})
            flash('Product is out of stock.', 'error')
            return redirect(request.referrer or url_for('customer.products'))
        
        if quantity > product.stock_quantity:
            message = f'Only {product.stock_quantity} items available in stock.'
            if request.is_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(request.referrer or url_for('customer.products'))
        
        # Check if item already in cart
        existing_item = CartItem.query.filter_by(user_id=user.id, product_id=product_id).first()
        
        if existing_item:
            new_quantity = existing_item.quantity + quantity
            if new_quantity > product.stock_quantity:
                message = f'Cannot add more items. Only {product.stock_quantity} available.'
                if request.is_json:
                    return jsonify({'success': False, 'message': message})
                flash(message, 'error')
                return redirect(request.referrer or url_for('customer.products'))
            existing_item.quantity = new_quantity
        else:
            cart_item = CartItem(user_id=user.id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)
        
        db.session.commit()
        success_message = f'{product.name} added to cart successfully!'
        
        if request.is_json:
            return jsonify({'success': True, 'message': success_message})
        flash(success_message, 'success')
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Cart error details: {error_details}")  # Detailed debug logging
        print(f"Cart error: {str(e)}")  # Debug logging
        error_message = 'Error adding item to cart. Please try again.'
        if request.is_json:
            return jsonify({'success': False, 'message': error_message})
        flash(error_message, 'error')
    
    return redirect(request.referrer or url_for('customer.products'))

@customer_bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    """Update cart item quantity"""
    user = get_current_user()
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
        item_id = int(data.get('item_id')) if data.get('item_id') else None
        quantity = int(data.get('quantity')) if data.get('quantity') is not None else None
    else:
        item_id = request.form.get('item_id', type=int)
        quantity = request.form.get('quantity', type=int)
    
    if not item_id or quantity < 0:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid request'})
        flash('Invalid request.', 'error')
        return redirect(url_for('customer.cart'))
    
    cart_item = CartItem.query.filter_by(id=item_id, user_id=user.id).first()
    if not cart_item:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Item not found'})
        flash('Item not found.', 'error')
        return redirect(url_for('customer.cart'))
    
    try:
        if quantity == 0:
            db.session.delete(cart_item)
            message = 'Item removed from cart.'
        else:
            if quantity > cart_item.product.stock_quantity:
                if request.is_json:
                    return jsonify({'success': False, 'message': f'Only {cart_item.product.stock_quantity} items available'})
                flash(f'Only {cart_item.product.stock_quantity} items available.', 'error')
                return redirect(url_for('customer.cart'))
            cart_item.quantity = quantity
            message = 'Cart updated.'
        
        db.session.commit()
        
        # Calculate new totals with tax
        cart_items = CartItem.query.filter_by(user_id=user.id).all()
        cart_subtotal = sum(item.total_price for item in cart_items)
        item_total = cart_item.total_price if quantity > 0 else 0
        
        # Get user's state for tax calculation
        user_state = user.state if user.state else 'DE'
        if len(user_state) > 2:
            state_mapping = {
                'delaware': 'DE', 'california': 'CA', 'new york': 'NY',
                'texas': 'TX', 'florida': 'FL', 'illinois': 'IL'
            }
            user_state = state_mapping.get(user_state.lower(), 'DE')
        
        # Calculate taxes
        tax_summary = None
        cart_total = cart_subtotal
        if cart_items:
            from src.utils.tax_calculator import tax_calculator
            cart_data = [{'product': item.product, 'quantity': item.quantity} for item in cart_items]
            tax_summary = tax_calculator.calculate_cart_tax(cart_data, user_state)
            cart_total = float(tax_summary['grand_total'])
        
        if request.is_json:
            response_data = {
                'success': True,
                'message': message,
                'item_total': float(item_total),
                'cart_subtotal': float(cart_subtotal),
                'cart_total': float(cart_total),
                'item_count': len(cart_items)
            }
            
            if tax_summary:
                response_data.update({
                    'excise_tax': float(tax_summary['total_excise_tax']),
                    'sales_tax': float(tax_summary['total_sales_tax']),
                    'total_tax': float(tax_summary['total_tax']),
                    'user_state': user_state
                })
            
            return jsonify(response_data)
        
        flash(message, 'success')
        return redirect(url_for('customer.cart'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Update cart error: {str(e)}")  # Debug logging
        if request.is_json:
            return jsonify({'success': False, 'message': 'Error updating cart'})
        flash('Error updating cart.', 'error')
        return redirect(url_for('customer.cart'))

@customer_bp.route('/cart/remove', methods=['POST'])
@customer_bp.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id=None):
    """Remove item from cart"""
    user = get_current_user()
    
    # Handle JSON requests
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        item_id = data.get('item_id')
    
    if not item_id:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Item ID required'})
        flash('Item not found.', 'error')
        return redirect(url_for('customer.cart'))
    
    cart_item = CartItem.query.filter_by(id=item_id, user_id=user.id).first()
    if not cart_item:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Item not found'})
        flash('Item not found.', 'error')
        return redirect(url_for('customer.cart'))
    
    try:
        db.session.delete(cart_item)
        db.session.commit()
        
        # Calculate new cart total
        cart_items = CartItem.query.filter_by(user_id=user.id).all()
        cart_total = sum(item.total_price for item in cart_items)
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Item removed from cart',
                'cart_total': float(cart_total)
            })
        
        flash('Item removed from cart.', 'info')
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'message': 'Error removing item from cart'})
        flash('Error removing item from cart.', 'error')
    
    return redirect(url_for('customer.cart'))

@customer_bp.route('/checkout')
@login_required
def checkout():
    """Checkout page with tax calculations"""
    user = get_current_user()
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('customer.products'))
    
    # Calculate basic total
    subtotal = sum(item.total_price for item in cart_items)
    
    # Try to calculate taxes, fallback to basic calculation if tax system fails
    try:
        from src.utils.tax_calculator import tax_calculator
        
        # Get user's state for tax calculation
        user_state = user.state if user.state else 'DE'
        if len(user_state) > 2:
            state_mapping = {
                'delaware': 'DE', 'california': 'CA', 'new york': 'NY',
                'texas': 'TX', 'florida': 'FL', 'illinois': 'IL'
            }
            user_state = state_mapping.get(user_state.lower(), 'DE')
        
        # Calculate taxes
        cart_data = [{'product': item.product, 'quantity': item.quantity} for item in cart_items]
        tax_summary = tax_calculator.calculate_cart_tax(cart_data, user_state)
        
        total = float(tax_summary['grand_total'])
        
        return render_template('customer/checkout.html',
                             cart_items=cart_items,
                             total=total,
                             tax_summary=tax_summary,
                             user_state=user_state,
                             user=user,
                             page_title='Checkout - MokTrading')
    
    except Exception as e:
        # Fallback to basic calculation without tax system
        print(f"Tax calculation error: {str(e)}")
        total = float(subtotal)
        
        return render_template('customer/checkout.html',
                             cart_items=cart_items,
                             total=total,
                             tax_summary=None,
                             user_state='DE',
                             user=user,
                             page_title='Checkout - MokTrading')

@customer_bp.route('/checkout/process', methods=['POST'])
@login_required
def process_checkout():
    """Process checkout and create order with tax calculations"""
    user = get_current_user()
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('customer.products'))
    
    # Get form data
    payment_method = request.form.get('payment_method')
    shipping_address = request.form.get('shipping_address', '').strip()
    notes = request.form.get('notes', '').strip()
    
    if not payment_method:
        flash('Please select a payment method.', 'error')
        return redirect(url_for('customer.checkout'))
    
    if not shipping_address:
        # Use user's default address
        shipping_address = f"{user.address}\n{user.city}, {user.state} {user.zip_code}".strip()
    
    # Calculate basic total
    subtotal = sum(item.total_price for item in cart_items)
    
    # Try to calculate taxes, fallback to basic calculation
    try:
        from src.utils.tax_calculator import tax_calculator
        
        # Get user's state for tax calculation
        user_state = user.state if user.state else 'DE'
        if len(user_state) > 2:
            state_mapping = {
                'delaware': 'DE', 'california': 'CA', 'new york': 'NY',
                'texas': 'TX', 'florida': 'FL', 'illinois': 'IL'
            }
            user_state = state_mapping.get(user_state.lower(), 'DE')
        
        # Calculate taxes
        cart_data = [{'product': item.product, 'quantity': item.quantity} for item in cart_items]
        tax_summary = tax_calculator.calculate_cart_tax(cart_data, user_state)
        
        # Create order with tax information
        order = Order(
            order_number=Order.generate_order_number(),
            user_id=user.id,
            subtotal=tax_summary['subtotal'],
            excise_tax=tax_summary['total_excise_tax'],
            sales_tax=tax_summary['total_sales_tax'],
            total_tax=tax_summary['total_tax'],
            total_amount=tax_summary['grand_total'],
            tax_state=user_state,
            payment_method=payment_method,
            shipping_address=shipping_address,
            notes=notes
        )
        
    except Exception as e:
        # Fallback to basic order without tax breakdown
        print(f"Tax calculation error in checkout: {str(e)}")
        order = Order(
            order_number=Order.generate_order_number(),
            user_id=user.id,
            subtotal=subtotal,
            excise_tax=0,
            sales_tax=0,
            total_tax=0,
            total_amount=subtotal,
            tax_state='DE',
            payment_method=payment_method,
            shipping_address=shipping_address,
            notes=notes
        )
    
    try:
        # Add order to database
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items and update stock
        for cart_item in cart_items:
            if cart_item.quantity > cart_item.product.stock_quantity:
                raise Exception(f'Insufficient stock for {cart_item.product.name}')
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
            
            # Update stock
            cart_item.product.stock_quantity -= cart_item.quantity
        
        # Clear cart
        for cart_item in cart_items:
            db.session.delete(cart_item)
        
        db.session.commit()
        
        # Send order notification to admin
        try:
            from src.utils.notifications import NotificationService
            notification_service = NotificationService()
            notification_service.send_order_notification(order, "new_order")
        except Exception as e:
            print(f"Notification error: {str(e)}")  # Log but don't fail the order
        
        flash(f'Order {order.order_number} placed successfully!', 'success')
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    except Exception as e:
        db.session.rollback()
        flash('Error processing order. Please try again.', 'error')
        return redirect(url_for('customer.checkout'))

@customer_bp.route('/orders')
@login_required
def orders():
    """Order history page"""
    user = get_current_user()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('customer/orders.html',
                         orders=orders,
                         page_title='Order History - MokTrading')

@customer_bp.route('/orders/<int:order_id>')
@customer_bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail page"""
    user = get_current_user()
    order = Order.query.filter_by(id=order_id, user_id=user.id).first_or_404()
    
    return render_template('customer/order_detail.html',
                         order=order,
                         page_title=f'Order {order.order_number} - MokTrading')

@customer_bp.route('/account')
@login_required
def account():
    """Customer account page"""
    user = get_current_user()
    recent_orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('customer/account.html',
                         user=user,
                         recent_orders=recent_orders,
                         page_title='My Account - MokTrading')


@customer_bp.route('/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    """Clear all items from cart"""
    user = get_current_user()
    
    try:
        # Delete all cart items for the user
        CartItem.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Cart cleared successfully'
            })
        
        flash('Cart cleared successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'message': 'Error clearing cart'})
        flash('Error clearing cart.', 'error')
    
    return redirect(url_for('customer.cart'))


@customer_bp.route('/cart/count')
@login_required
def cart_count():
    """Get cart item count"""
    user = get_current_user()
    count = CartItem.query.filter_by(user_id=user.id).count()
    return jsonify({'count': count})

