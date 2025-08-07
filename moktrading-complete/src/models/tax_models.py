"""
Tax Models for State Tobacco Tax Calculations
Handles cigarette, cigar, vape, and sales tax calculations by state
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Tuple
import json

class StateTobaccoTax:
    """Comprehensive state tobacco tax calculator for all 50 states + DC"""
    
    def __init__(self):
        self.tax_data = self._load_tax_data()
    
    def _load_tax_data(self) -> Dict:
        """Load comprehensive tax data for all states"""
        return {
            'AL': {  # Alabama
                'cigarette_tax': Decimal('0.675'),
                'cigar_tax': {'type': 'per_unit', 'rate': Decimal('0.0405')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.04')
            },
            'AK': {  # Alaska
                'cigarette_tax': Decimal('2.000'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.75')},
                'vape_tax': None,
                'sales_tax_applies': False,
                'sales_tax_rate': Decimal('0.00')
            },
            'AZ': {  # Arizona
                'cigarette_tax': Decimal('2.000'),
                'cigar_tax': {'type': 'per_unit', 'rate': Decimal('0.218')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.056')
            },
            'AR': {  # Arkansas
                'cigarette_tax': Decimal('1.150'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.68'), 'cap': Decimal('0.50')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.065')
            },
            'CA': {  # California
                'cigarette_tax': Decimal('2.870'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.5427')},
                'vape_tax': {'type': 'dual', 'wholesale': Decimal('0.5632'), 'retail': Decimal('0.125')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.0725')
            },
            'CO': {  # Colorado
                'cigarette_tax': Decimal('1.940'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.56')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.50')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.029')
            },
            'CT': {  # Connecticut
                'cigarette_tax': Decimal('4.350'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.50'), 'cap': Decimal('0.50')},
                'vape_tax': {'type': 'bifurcated', 'open': Decimal('0.10'), 'closed': Decimal('0.40')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.0635')
            },
            'DE': {  # Delaware - Your home state
                'cigarette_tax': Decimal('2.100'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.30')},
                'vape_tax': {'type': 'per_ml', 'rate': Decimal('0.05')},
                'sales_tax_applies': False,
                'sales_tax_rate': Decimal('0.00')
            },
            'DC': {  # District of Columbia
                'cigarette_tax': Decimal('4.500'),
                'cigar_tax': {'type': 'none'},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.79')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'FL': {  # Florida
                'cigarette_tax': Decimal('1.339'),
                'cigar_tax': {'type': 'none'},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'GA': {  # Georgia
                'cigarette_tax': Decimal('0.370'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.23')},
                'vape_tax': {'type': 'bifurcated', 'open': Decimal('0.07'), 'closed': Decimal('0.05')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.04')
            },
            'HI': {  # Hawaii
                'cigarette_tax': Decimal('3.200'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.50')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.70')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.04')
            },
            'ID': {  # Idaho
                'cigarette_tax': Decimal('0.570'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.40'), 'cap': Decimal('0.50')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'IL': {  # Illinois
                'cigarette_tax': Decimal('2.980'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.45')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.15')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.0625')
            },
            'IN': {  # Indiana
                'cigarette_tax': Decimal('0.995'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.30'), 'cap': Decimal('3.00')},
                'vape_tax': {'type': 'bifurcated', 'open': Decimal('0.15'), 'closed': Decimal('0.15')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.07')
            },
            'IA': {  # Iowa
                'cigarette_tax': Decimal('1.360'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.50'), 'cap': Decimal('0.50')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'KS': {  # Kansas
                'cigarette_tax': Decimal('1.290'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.10')},
                'vape_tax': {'type': 'per_ml', 'rate': Decimal('0.05')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.065')
            },
            'KY': {  # Kentucky
                'cigarette_tax': Decimal('1.100'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.15')},
                'vape_tax': {'type': 'bifurcated', 'open': Decimal('0.15'), 'closed': Decimal('1.50')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'LA': {  # Louisiana
                'cigarette_tax': Decimal('1.080'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.20')},
                'vape_tax': {'type': 'per_ml', 'rate': Decimal('0.15')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.0445')
            },
            'ME': {  # Maine
                'cigarette_tax': Decimal('2.000'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.43')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.43')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.055')
            },
            'MD': {  # Maryland
                'cigarette_tax': Decimal('3.750'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.15')},
                'vape_tax': {'type': 'bifurcated', 'open': Decimal('0.12'), 'closed': Decimal('0.60')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'MA': {  # Massachusetts
                'cigarette_tax': Decimal('3.510'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.40')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.75')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.0625')
            },
            'MI': {  # Michigan
                'cigarette_tax': Decimal('2.000'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.32'), 'cap': Decimal('0.50')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'MN': {  # Minnesota
                'cigarette_tax': Decimal('3.040'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.95'), 'cap': Decimal('0.50')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.95')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06875')
            },
            'MS': {  # Mississippi
                'cigarette_tax': Decimal('0.680'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.15')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.07')
            },
            'MO': {  # Missouri
                'cigarette_tax': Decimal('0.170'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.10')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.04225')
            },
            'MT': {  # Montana
                'cigarette_tax': Decimal('1.700'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.50'), 'cap': Decimal('0.35')},
                'vape_tax': None,
                'sales_tax_applies': False,
                'sales_tax_rate': Decimal('0.00')
            },
            'NE': {  # Nebraska
                'cigarette_tax': Decimal('0.640'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.20')},
                'vape_tax': {'type': 'bifurcated', 'small': Decimal('0.05'), 'large': Decimal('0.10')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.055')
            },
            'NV': {  # Nevada
                'cigarette_tax': Decimal('1.800'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.30')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.30')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.0685')
            },
            'NH': {  # New Hampshire
                'cigarette_tax': Decimal('1.780'),
                'cigar_tax': {'type': 'none'},
                'vape_tax': {'type': 'bifurcated', 'open': Decimal('0.08'), 'closed': Decimal('0.30')},
                'sales_tax_applies': False,
                'sales_tax_rate': Decimal('0.00')
            },
            'NJ': {  # New Jersey
                'cigarette_tax': Decimal('2.700'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.30')},
                'vape_tax': {'type': 'bifurcated', 'open': Decimal('0.10'), 'closed': Decimal('0.10')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06625')
            },
            'NM': {  # New Mexico
                'cigarette_tax': Decimal('2.000'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.25'), 'cap': Decimal('0.50')},
                'vape_tax': {'type': 'bifurcated', 'open': Decimal('0.125'), 'closed': Decimal('0.50')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.05125')
            },
            'NY': {  # New York
                'cigarette_tax': Decimal('5.350'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.75')},
                'vape_tax': {'type': 'retail', 'rate': Decimal('0.20')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.08')
            },
            'NC': {  # North Carolina
                'cigarette_tax': Decimal('0.450'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.1285')},
                'vape_tax': {'type': 'per_ml', 'rate': Decimal('0.05')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.0475')
            },
            'ND': {  # North Dakota
                'cigarette_tax': Decimal('0.440'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.28')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.05')
            },
            'OH': {  # Ohio
                'cigarette_tax': Decimal('1.600'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.17'), 'cap': Decimal('0.65')},
                'vape_tax': {'type': 'per_ml', 'rate': Decimal('0.10')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.0575')
            },
            'OK': {  # Oklahoma
                'cigarette_tax': Decimal('2.030'),
                'cigar_tax': {'type': 'per_unit', 'rate': Decimal('0.12')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.045')
            },
            'OR': {  # Oregon
                'cigarette_tax': Decimal('3.330'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.65'), 'cap': Decimal('1.00')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.65')},
                'sales_tax_applies': False,
                'sales_tax_rate': Decimal('0.00')
            },
            'PA': {  # Pennsylvania
                'cigarette_tax': Decimal('2.600'),
                'cigar_tax': {'type': 'none'},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.40')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'RI': {  # Rhode Island
                'cigarette_tax': Decimal('4.250'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.80'), 'cap': Decimal('0.50')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.07')
            },
            'SC': {  # South Carolina
                'cigarette_tax': Decimal('0.570'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.055')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'SD': {  # South Dakota
                'cigarette_tax': Decimal('1.530'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.35')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.045')
            },
            'TN': {  # Tennessee
                'cigarette_tax': Decimal('0.620'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.066')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.07')
            },
            'TX': {  # Texas
                'cigarette_tax': Decimal('1.410'),
                'cigar_tax': {'type': 'per_unit', 'rate': Decimal('0.011')},
                'vape_tax': None,
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.0625')
            },
            'UT': {  # Utah
                'cigarette_tax': Decimal('1.700'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.86')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.56')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.0485')
            },
            'VT': {  # Vermont
                'cigarette_tax': Decimal('3.080'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.92'), 'cap_low': Decimal('2.00'), 'cap_high': Decimal('4.00')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.92')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'VA': {  # Virginia
                'cigarette_tax': Decimal('0.600'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.20')},
                'vape_tax': {'type': 'per_ml', 'rate': Decimal('0.066')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.053')
            },
            'WA': {  # Washington
                'cigarette_tax': Decimal('3.025'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.95'), 'cap': Decimal('0.65')},
                'vape_tax': {'type': 'bifurcated', 'open': Decimal('0.09'), 'closed': Decimal('0.27')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.065')
            },
            'WV': {  # West Virginia
                'cigarette_tax': Decimal('1.200'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.12')},
                'vape_tax': {'type': 'per_ml', 'rate': Decimal('0.075')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.06')
            },
            'WI': {  # Wisconsin
                'cigarette_tax': Decimal('2.520'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.71'), 'cap': Decimal('0.50')},
                'vape_tax': {'type': 'per_ml', 'rate': Decimal('0.05')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.05')
            },
            'WY': {  # Wyoming
                'cigarette_tax': Decimal('0.600'),
                'cigar_tax': {'type': 'percentage', 'rate': Decimal('0.20')},
                'vape_tax': {'type': 'percentage', 'rate': Decimal('0.15')},
                'sales_tax_applies': True,
                'sales_tax_rate': Decimal('0.04')
            }
        }
    
    def calculate_cigarette_tax(self, state: str, quantity: int = 1) -> Decimal:
        """Calculate cigarette excise tax for given state and quantity (packs)"""
        if state not in self.tax_data:
            return Decimal('0')
        
        tax_per_pack = self.tax_data[state]['cigarette_tax']
        return tax_per_pack * Decimal(str(quantity))
    
    def calculate_cigar_tax(self, state: str, wholesale_price: Decimal, quantity: int = 1) -> Decimal:
        """Calculate cigar excise tax for given state, price, and quantity"""
        if state not in self.tax_data:
            return Decimal('0')
        
        cigar_tax_info = self.tax_data[state]['cigar_tax']
        
        if cigar_tax_info['type'] == 'none':
            return Decimal('0')
        
        if cigar_tax_info['type'] == 'percentage':
            tax_per_unit = wholesale_price * cigar_tax_info['rate']
            
            # Apply caps if they exist
            if 'cap' in cigar_tax_info:
                tax_per_unit = min(tax_per_unit, cigar_tax_info['cap'])
            elif 'cap_low' in cigar_tax_info and 'cap_high' in cigar_tax_info:
                # Vermont special case
                if wholesale_price < Decimal('10'):
                    tax_per_unit = min(tax_per_unit, cigar_tax_info['cap_low'])
                else:
                    tax_per_unit = min(tax_per_unit, cigar_tax_info['cap_high'])
            
            return tax_per_unit * Decimal(str(quantity))
        
        elif cigar_tax_info['type'] == 'per_unit':
            return cigar_tax_info['rate'] * Decimal(str(quantity))
        
        return Decimal('0')
    
    def calculate_vape_tax(self, state: str, product_type: str, price: Decimal = None, 
                          volume_ml: Decimal = None, quantity: int = 1) -> Decimal:
        """
        Calculate vape/e-cigarette tax
        product_type: 'open', 'closed', 'cartridge'
        price: wholesale or retail price depending on tax type
        volume_ml: volume in milliliters for per-ml taxes
        """
        if state not in self.tax_data:
            return Decimal('0')
        
        vape_tax_info = self.tax_data[state]['vape_tax']
        
        if not vape_tax_info:
            return Decimal('0')
        
        if vape_tax_info['type'] == 'percentage':
            if price:
                return price * vape_tax_info['rate'] * Decimal(str(quantity))
        
        elif vape_tax_info['type'] == 'per_ml':
            if volume_ml:
                return volume_ml * vape_tax_info['rate'] * Decimal(str(quantity))
        
        elif vape_tax_info['type'] == 'bifurcated':
            if product_type == 'open' and 'open' in vape_tax_info:
                if 'open' in vape_tax_info and isinstance(vape_tax_info['open'], Decimal):
                    # Percentage rate
                    if price:
                        return price * vape_tax_info['open'] * Decimal(str(quantity))
                    elif volume_ml:
                        return volume_ml * vape_tax_info['open'] * Decimal(str(quantity))
            elif product_type == 'closed' and 'closed' in vape_tax_info:
                if isinstance(vape_tax_info['closed'], Decimal):
                    if vape_tax_info['closed'] < Decimal('1'):  # Percentage
                        if price:
                            return price * vape_tax_info['closed'] * Decimal(str(quantity))
                    else:  # Per unit or per mL
                        if volume_ml:
                            return volume_ml * vape_tax_info['closed'] * Decimal(str(quantity))
                        else:
                            return vape_tax_info['closed'] * Decimal(str(quantity))
        
        elif vape_tax_info['type'] == 'dual':
            # California special case - both wholesale and retail tax
            total_tax = Decimal('0')
            if price and 'wholesale' in vape_tax_info:
                total_tax += price * vape_tax_info['wholesale']
            if price and 'retail' in vape_tax_info:
                total_tax += price * vape_tax_info['retail']
            return total_tax * Decimal(str(quantity))
        
        return Decimal('0')
    
    def calculate_sales_tax(self, state: str, taxable_amount: Decimal) -> Decimal:
        """Calculate sales tax if applicable in the state"""
        if state not in self.tax_data:
            return Decimal('0')
        
        if not self.tax_data[state]['sales_tax_applies']:
            return Decimal('0')
        
        return taxable_amount * self.tax_data[state]['sales_tax_rate']
    
    def calculate_total_tax(self, state: str, product_type: str, base_price: Decimal,
                           quantity: int = 1, volume_ml: Decimal = None) -> Dict[str, Decimal]:
        """
        Calculate total tax burden for a tobacco product
        Returns breakdown of all applicable taxes
        """
        taxes = {
            'excise_tax': Decimal('0'),
            'sales_tax': Decimal('0'),
            'total_tax': Decimal('0')
        }
        
        # Calculate excise tax based on product type
        if product_type == 'cigarettes':
            taxes['excise_tax'] = self.calculate_cigarette_tax(state, quantity)
        elif product_type in ['cigars', 'cigar']:
            taxes['excise_tax'] = self.calculate_cigar_tax(state, base_price, quantity)
        elif product_type in ['vape', 'e-cigarette', 'vape_open', 'vape_closed']:
            vape_type = 'open' if 'open' in product_type else 'closed'
            taxes['excise_tax'] = self.calculate_vape_tax(state, vape_type, base_price, volume_ml, quantity)
        
        # Calculate sales tax on base price + excise tax
        taxable_amount = base_price + taxes['excise_tax']
        taxes['sales_tax'] = self.calculate_sales_tax(state, taxable_amount)
        
        # Total tax burden
        taxes['total_tax'] = taxes['excise_tax'] + taxes['sales_tax']
        
        return taxes
    
    def get_state_info(self, state: str) -> Dict:
        """Get complete tax information for a state"""
        return self.tax_data.get(state, {})
    
    def requires_wholesaler_license(self, state: str) -> bool:
        """Check if state requires wholesaler licensing (simplified - would need detailed research)"""
        # Most states require some form of tobacco wholesaler licensing
        no_license_states = ['DE', 'MT', 'NH', 'OR']  # Simplified list
        return state not in no_license_states
    
    def get_filing_requirements(self, state: str) -> Dict[str, str]:
        """Get filing and reporting requirements (simplified)"""
        # This would need detailed research for each state
        return {
            'frequency': 'Monthly',  # Most common
            'due_date': '20th of following month',  # Most common
            'registration_required': 'Yes' if self.requires_wholesaler_license(state) else 'No',
            'bond_required': 'Varies by state',
            'notes': 'Consult state tobacco tax authority for specific requirements'
        }

