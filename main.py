import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
from src.models.unified_models import db, User, Category, Product, CartItem
from src.routes.auth import auth_bp
from src.routes.customer import customer_bp
from src.routes.admin import admin_bp
from src.utils.auth import get_current_user
# from src.utils.scheduler import report_scheduler
import secrets

# Create Flask app
app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
           static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Enable CORS for cross-origin requests
CORS(app)

# Initialize database
db.init_app(app)

# Initialize scheduler
# report_scheduler.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(customer_bp, url_prefix='/')
app.register_blueprint(admin_bp, url_prefix='/admin')

# Import and register tax blueprint
from src.routes.tax_api import tax_bp
app.register_blueprint(tax_bp, url_prefix='/tax')

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Template context processors
@app.context_processor
def inject_user():
    """Inject current user into all templates"""
    return dict(current_user=get_current_user())

@app.context_processor
def inject_cart_count():
    """Inject cart item count into all templates"""
    cart_count = 0
    if 'user_id' in session:
        cart_count = CartItem.query.filter_by(user_id=session['user_id']).count()
    return dict(cart_count=cart_count)

@app.context_processor
def inject_categories():
    """Inject active categories into all templates"""
    categories = Category.query.filter_by(is_active=True).all()
    return dict(categories=categories)

# Main routes
@app.route('/')
def home():
    """Home page - redirect to customer home"""
    return redirect(url_for('customer.home'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

# Initialize database and create sample data
def init_database():
    """Initialize database with sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we already have data
        if User.query.first() is not None:
            return
        
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@moktrading.com',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # Create sample customer
        customer = User(
            username='customer',
            email='customer@example.com',
            first_name='John',
            last_name='Doe',
            phone='555-0123',
            address='123 Main St',
            city='Anytown',
            state='CA',
            zip_code='12345'
        )
        customer.set_password('customer123')
        db.session.add(customer)
        
        # Create categories
        categories_data = [
            {'name': 'Cigarettes', 'description': 'Premium cigarettes from top brands'},
            {'name': 'Cigars', 'description': 'Fine cigars for connoisseurs'},
            {'name': 'Pipe Tobacco', 'description': 'Quality pipe tobacco blends'},
            {'name': 'Rolling Papers', 'description': 'Papers and accessories for rolling'},
            {'name': 'Accessories', 'description': 'Smoking accessories and tools'}
        ]
        
        categories = []
        for cat_data in categories_data:
            category = Category(**cat_data)
            categories.append(category)
            db.session.add(category)
        
        db.session.commit()
        
        # Create sample products
        products_data = [
            {
                'name': 'Marlboro Gold',
                'description': 'Premium light cigarettes with smooth taste and refined flavor profile',
                'price': 12.99,
                'stock_quantity': 100,
                'category_id': categories[0].id,
                'brand': 'Marlboro',
                'is_featured': True
            },
            {
                'name': 'Camel Turkish Royal',
                'description': 'Rich Turkish blend cigarettes with distinctive aroma and full-bodied taste',
                'price': 13.49,
                'stock_quantity': 85,
                'category_id': categories[0].id,
                'brand': 'Camel',
                'is_featured': True
            },
            {
                'name': 'Romeo y Julieta Churchill',
                'description': 'Classic Cuban-style cigars with complex flavor notes and smooth finish',
                'price': 45.99,
                'stock_quantity': 25,
                'category_id': categories[1].id,
                'brand': 'Romeo y Julieta',
                'is_featured': True
            },
            {
                'name': 'Montecristo No. 2',
                'description': 'Premium torpedo cigars with rich, full-bodied flavor and excellent construction',
                'price': 52.99,
                'stock_quantity': 30,
                'category_id': categories[1].id,
                'brand': 'Montecristo'
            },
            {
                'name': 'Captain Black Original',
                'description': 'Mild and aromatic pipe tobacco with sweet vanilla notes',
                'price': 8.99,
                'stock_quantity': 50,
                'category_id': categories[2].id,
                'brand': 'Captain Black'
            },
            {
                'name': 'Dunhill Early Morning Pipe',
                'description': 'English breakfast blend pipe tobacco with Oriental and Virginia tobaccos',
                'price': 15.99,
                'stock_quantity': 40,
                'category_id': categories[2].id,
                'brand': 'Dunhill'
            },
            {
                'name': 'RAW Classic Rolling Papers',
                'description': 'Natural unrefined rolling papers made from pure hemp',
                'price': 2.99,
                'stock_quantity': 200,
                'category_id': categories[3].id,
                'brand': 'RAW',
                'is_featured': True
            },
            {
                'name': 'Zippo Classic Lighter',
                'description': 'Windproof lighter with lifetime guarantee and iconic design',
                'price': 24.99,
                'stock_quantity': 75,
                'category_id': categories[4].id,
                'brand': 'Zippo'
            },
            {
                'name': 'Newport Menthol',
                'description': 'Cool menthol cigarettes with refreshing taste',
                'price': 11.99,
                'stock_quantity': 90,
                'category_id': categories[0].id,
                'brand': 'Newport'
            },
            {
                'name': 'Cohiba Robusto',
                'description': 'Premium Cuban cigars with exceptional quality and flavor',
                'price': 65.99,
                'stock_quantity': 15,
                'category_id': categories[1].id,
                'brand': 'Cohiba',
                'is_featured': True
            }
        ]
        
        for product_data in products_data:
            product = Product(**product_data)
            db.session.add(product)
        
        db.session.commit()
        print("Database initialized with sample data!")

if __name__ == '__main__':
    init_database()
    
    # Start the automated report scheduler
    # report_scheduler.start_scheduler()
    
    app.run(host='0.0.0.0', port=5000, debug=True)

