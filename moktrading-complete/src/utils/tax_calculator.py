"""
Tax Calculator Utility for MokTrading E-Commerce System
Integrates with existing product and order models
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional
from src.models.tax_models import StateTobaccoTax
from src.models.unified_models import Product, OrderItem

class TaxCalculator:
    """Main tax calculation utility for the e-commerce system"""
    
    def __init__(self):
        self.state_tax = StateTobaccoTax()
    
    def calculate_product_tax(self, product: Product, state: str, quantity: int = 1) -> Dict[str, Decimal]:
        """
        Calculate tax for a specific product in a specific state
        Returns detailed tax breakdown
        """
        # Determine product type from category
        product_type = self._get_product_type(product)
        
        # Get base price (wholesale price for tax calculation)
        base_price = Decimal(str(product.price))
        
        # Get volume for vape products if available
        volume_ml = self._extract_volume_ml(product)
        
        # Calculate taxes
        tax_breakdown = self.state_tax.calculate_total_tax(
            state=state,
            product_type=product_type,
            base_price=base_price,
            quantity=quantity,
            volume_ml=volume_ml
        )
        
        # Add product-specific information
        tax_breakdown.update({
            'product_id': product.id,
            'product_name': product.name,
            'product_type': product_type,
            'base_price': base_price,
            'quantity': quantity,
            'state': state,
            'price_with_tax': base_price + tax_breakdown['total_tax']
        })
        
        return tax_breakdown
    
    def calculate_cart_tax(self, cart_items: List[Dict], shipping_state: str) -> Dict[str, any]:
        """
        Calculate tax for entire shopping cart
        cart_items: List of {'product': Product, 'quantity': int}
        """
        cart_tax_summary = {
            'items': [],
            'subtotal': Decimal('0'),
            'total_excise_tax': Decimal('0'),
            'total_sales_tax': Decimal('0'),
            'total_tax': Decimal('0'),
            'grand_total': Decimal('0'),
            'state': shipping_state
        }
        
        for item in cart_items:
            product = item['product']
            quantity = item['quantity']
            
            # Calculate tax for this item
            item_tax = self.calculate_product_tax(product, shipping_state, quantity)
            
            # Add to cart summary
            cart_tax_summary['items'].append(item_tax)
            cart_tax_summary['subtotal'] += item_tax['base_price']
            cart_tax_summary['total_excise_tax'] += item_tax['excise_tax']
            cart_tax_summary['total_sales_tax'] += item_tax['sales_tax']
            cart_tax_summary['total_tax'] += item_tax['total_tax']
        
        cart_tax_summary['grand_total'] = cart_tax_summary['subtotal'] + cart_tax_summary['total_tax']
        
        return cart_tax_summary
    
    def calculate_order_tax(self, order_items: List[OrderItem], shipping_state: str) -> Dict[str, Decimal]:
        """Calculate tax for an existing order"""
        cart_items = []
        for order_item in order_items:
            cart_items.append({
                'product': order_item.product,
                'quantity': order_item.quantity
            })
        
        return self.calculate_cart_tax(cart_items, shipping_state)
    
    def get_tax_rate_summary(self, state: str) -> Dict[str, any]:
        """Get summary of all tax rates for a state"""
        state_info = self.state_tax.get_state_info(state)
        
        if not state_info:
            return {'error': f'State {state} not found'}
        
        summary = {
            'state': state,
            'cigarette_tax_per_pack': float(state_info['cigarette_tax']),
            'cigar_tax': self._format_tax_info(state_info['cigar_tax']),
            'vape_tax': self._format_tax_info(state_info['vape_tax']),
            'sales_tax_applies': state_info['sales_tax_applies'],
            'sales_tax_rate': float(state_info['sales_tax_rate']) if state_info['sales_tax_applies'] else 0,
            'wholesaler_license_required': self.state_tax.requires_wholesaler_license(state),
            'filing_requirements': self.state_tax.get_filing_requirements(state)
        }
        
        return summary
    
    def _get_product_type(self, product: Product) -> str:
        """Determine product type from product category or name"""
        category_lower = product.category.name.lower() if product.category else ''
        name_lower = product.name.lower()
        
        if 'cigarette' in category_lower or 'cigarette' in name_lower:
            return 'cigarettes'
        elif 'cigar' in category_lower or 'cigar' in name_lower:
            return 'cigars'
        elif any(term in category_lower or term in name_lower for term in ['vape', 'e-cig', 'electronic', 'vapor']):
            # Try to determine if open or closed system
            if any(term in name_lower for term in ['cartridge', 'pod', 'disposable']):
                return 'vape_closed'
            else:
                return 'vape_open'
        else:
            # Default to other tobacco products (treated as cigars for tax purposes)
            return 'cigars'
    
    def _extract_volume_ml(self, product: Product) -> Optional[Decimal]:
        """Extract volume in mL from product description for vape products"""
        import re
        
        # Look for volume in product name or description
        text = f"{product.name} {product.description or ''}".lower()
        
        # Common patterns: "30ml", "30 ml", "3.0ml", etc.
        ml_patterns = [
            r'(\d+(?:\.\d+)?)\s*ml',
            r'(\d+(?:\.\d+)?)\s*milliliter',
            r'(\d+(?:\.\d+)?)\s*mL'
        ]
        
        for pattern in ml_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return Decimal(match.group(1))
                except:
                    continue
        
        # Default volume assumptions for common vape products
        if 'cartridge' in text or 'pod' in text:
            return Decimal('1.0')  # Typical cartridge size
        elif 'disposable' in text:
            return Decimal('2.0')  # Typical disposable size
        
        return None
    
    def _format_tax_info(self, tax_info) -> Dict[str, any]:
        """Format tax information for display"""
        if not tax_info:
            return {'type': 'none', 'description': 'No tax'}
        
        if tax_info['type'] == 'none':
            return {'type': 'none', 'description': 'No tax'}
        
        elif tax_info['type'] == 'percentage':
            rate_percent = float(tax_info['rate']) * 100
            desc = f"{rate_percent:.2f}% of wholesale price"
            if 'cap' in tax_info:
                desc += f" (capped at ${float(tax_info['cap']):.2f})"
            return {'type': 'percentage', 'rate': rate_percent, 'description': desc}
        
        elif tax_info['type'] == 'per_unit':
            rate = float(tax_info['rate'])
            return {'type': 'per_unit', 'rate': rate, 'description': f"${rate:.3f} per unit"}
        
        elif tax_info['type'] == 'per_ml':
            rate = float(tax_info['rate'])
            return {'type': 'per_ml', 'rate': rate, 'description': f"${rate:.3f} per mL"}
        
        elif tax_info['type'] == 'bifurcated':
            return {'type': 'bifurcated', 'description': 'Different rates for open/closed systems'}
        
        else:
            return {'type': 'complex', 'description': 'Complex tax structure - see details'}

# Global instance for easy import
tax_calculator = TaxCalculator()

