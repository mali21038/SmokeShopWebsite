"""
Tax API Routes for MokTrading System
Provides tax calculation and state tax information endpoints
"""

from flask import Blueprint, request, jsonify, render_template
from src.utils.tax_calculator import tax_calculator
from src.models.unified_models import Product
from src.utils.auth import admin_required
import json

tax_bp = Blueprint('tax', __name__, url_prefix='/tax')

@tax_bp.route('/calculate', methods=['POST'])
def calculate_tax():
    """API endpoint to calculate tax for products"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        state = data.get('state', 'DE')
        items = data.get('items', [])
        
        if not items:
            return jsonify({'error': 'No items provided'}), 400
        
        # Convert items to cart format
        cart_items = []
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': f'Product {product_id} not found'}), 404
            
            cart_items.append({
                'product': product,
                'quantity': quantity
            })
        
        # Calculate taxes
        tax_summary = tax_calculator.calculate_cart_tax(cart_items, state)
        
        # Convert Decimal to float for JSON serialization
        result = {
            'state': state,
            'subtotal': float(tax_summary['subtotal']),
            'total_excise_tax': float(tax_summary['total_excise_tax']),
            'total_sales_tax': float(tax_summary['total_sales_tax']),
            'total_tax': float(tax_summary['total_tax']),
            'grand_total': float(tax_summary['grand_total']),
            'items': []
        }
        
        for item_tax in tax_summary['items']:
            result['items'].append({
                'product_id': item_tax['product_id'],
                'product_name': item_tax['product_name'],
                'product_type': item_tax['product_type'],
                'base_price': float(item_tax['base_price']),
                'quantity': item_tax['quantity'],
                'excise_tax': float(item_tax['excise_tax']),
                'sales_tax': float(item_tax['sales_tax']),
                'total_tax': float(item_tax['total_tax']),
                'price_with_tax': float(item_tax['price_with_tax'])
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tax_bp.route('/state/<state_code>')
def get_state_tax_info(state_code):
    """Get tax information for a specific state"""
    try:
        state_code = state_code.upper()
        tax_info = tax_calculator.get_tax_rate_summary(state_code)
        
        if 'error' in tax_info:
            return jsonify(tax_info), 404
        
        return jsonify(tax_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tax_bp.route('/states')
def get_all_states_tax_info():
    """Get tax information for all states"""
    try:
        states = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
            'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
            'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
            'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
            'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
        
        all_states_info = {}
        for state in states:
            all_states_info[state] = tax_calculator.get_tax_rate_summary(state)
        
        return jsonify(all_states_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tax_bp.route('/admin/dashboard')
@admin_required
def tax_dashboard():
    """Admin tax dashboard"""
    return render_template('admin/tax_dashboard.html',
                         page_title='Tax Management - MokTrading Admin')

@tax_bp.route('/admin/compliance')
@admin_required
def tax_compliance():
    """Tax compliance information page"""
    # Get all states tax info for compliance overview
    states = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
        'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
        'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
        'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
        'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    ]
    
    states_info = []
    for state in states:
        info = tax_calculator.get_tax_rate_summary(state)
        if 'error' not in info:
            states_info.append(info)
    
    return render_template('admin/tax_compliance.html',
                         states_info=states_info,
                         page_title='Tax Compliance - MokTrading Admin')

@tax_bp.route('/admin/calculator')
@admin_required
def tax_calculator_tool():
    """Interactive tax calculator tool for admins"""
    products = Product.query.filter_by(is_active=True).all()
    
    return render_template('admin/tax_calculator.html',
                         products=products,
                         page_title='Tax Calculator - MokTrading Admin')

