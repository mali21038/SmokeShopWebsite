import schedule
import time
import threading
from datetime import datetime, timedelta
from sqlalchemy import func
from src.models.unified_models import db, Order, OrderItem, Product, User, CartItem
from src.utils.notifications import notification_service
import logging

logger = logging.getLogger(__name__)

class ReportingService:
    """Automated reporting service for daily and weekly business reports"""
    
    def __init__(self, app=None):
        self.app = app
        self.scheduler_thread = None
        self.running = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the reporting service with Flask app"""
        self.app = app
        
        # Schedule reports
        schedule.every().day.at("23:30").do(self._run_daily_report)
        schedule.every().sunday.at("23:45").do(self._run_weekly_report)
        schedule.every().day.at("01:00").do(self._cleanup_old_data)
        
        # Start scheduler in background thread
        self.start_scheduler()
    
    def start_scheduler(self):
        """Start the background scheduler"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logger.info("Automated reporting scheduler started")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Automated reporting scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in background thread"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _run_daily_report(self):
        """Generate and send daily report"""
        try:
            with self.app.app_context():
                logger.info("Generating daily report...")
                report_data = self.generate_daily_report()
                success = notification_service.send_daily_report(report_data)
                
                if success:
                    logger.info("Daily report sent successfully")
                else:
                    logger.error("Failed to send daily report")
                    
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
    
    def _run_weekly_report(self):
        """Generate and send weekly report"""
        try:
            with self.app.app_context():
                logger.info("Generating weekly report...")
                report_data = self.generate_weekly_report()
                success = notification_service.send_weekly_report(report_data)
                
                if success:
                    logger.info("Weekly report sent successfully")
                else:
                    logger.error("Failed to send weekly report")
                    
        except Exception as e:
            logger.error(f"Error generating weekly report: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old temporary data"""
        try:
            with self.app.app_context():
                # Clean up old cart items (older than 30 days)
                cutoff_date = datetime.now() - timedelta(days=30)
                old_carts = CartItem.query.filter(CartItem.created_at < cutoff_date).all()
                
                for cart_item in old_carts:
                    db.session.delete(cart_item)
                
                db.session.commit()
                logger.info(f"Cleaned up {len(old_carts)} old cart items")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def generate_daily_report(self):
        """Generate daily business report data"""
        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            # Orders data
            daily_orders = Order.query.filter(
                Order.created_at >= start_of_day,
                Order.created_at <= end_of_day
            ).all()
            
            total_orders = len(daily_orders)
            total_revenue = sum(float(order.total_amount) for order in daily_orders)
            
            # Payment breakdown
            cash_payments = sum(float(order.total_amount) for order in daily_orders 
                              if order.payment_method == 'cash' and order.payment_status == 'paid')
            credit_payments = sum(float(order.total_amount) for order in daily_orders 
                                if order.payment_method == 'credit' and order.payment_status == 'paid')
            pending_payments = sum(float(order.total_amount) for order in daily_orders 
                                 if order.payment_status == 'pending')
            
            # Order status breakdown
            completed_orders = len([o for o in daily_orders if o.status == 'completed'])
            processing_orders = len([o for o in daily_orders if o.status == 'processing'])
            pending_orders = len([o for o in daily_orders if o.status == 'pending'])
            
            # Customer data
            new_customers = User.query.filter(
                User.role == 'customer',
                User.created_at >= start_of_day,
                User.created_at <= end_of_day
            ).count()
            
            active_carts = db.session.query(CartItem.user_id).distinct().count()
            
            # Top products
            top_products = db.session.query(
                Product.name,
                func.sum(OrderItem.quantity).label('total_sold'),
                func.sum(OrderItem.quantity * OrderItem.price).label('revenue')
            ).join(OrderItem).join(Order).filter(
                Order.created_at >= start_of_day,
                Order.created_at <= end_of_day
            ).group_by(Product.id).order_by(
                func.sum(OrderItem.quantity * OrderItem.price).desc()
            ).limit(5).all()
            
            top_products_text = ""
            for i, (name, sold, revenue) in enumerate(top_products, 1):
                top_products_text += f"{i}. {name} - {sold} sold (${revenue:.2f})\\n"
            
            return {
                'date': today.strftime('%Y-%m-%d'),
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'cash_payments': cash_payments,
                'credit_payments': credit_payments,
                'pending_payments': pending_payments,
                'completed_orders': completed_orders,
                'processing_orders': processing_orders,
                'pending_orders': pending_orders,
                'new_customers': new_customers,
                'active_carts': active_carts,
                'top_products_text': top_products_text or 'No sales today'
            }
            
        except Exception as e:
            logger.error(f"Error generating daily report data: {str(e)}")
            return {}
    
    def generate_weekly_report(self):
        """Generate weekly business report data"""
        try:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            start_of_week = datetime.combine(week_start, datetime.min.time())
            end_of_week = datetime.combine(week_end, datetime.max.time())
            
            # Weekly orders
            weekly_orders = Order.query.filter(
                Order.created_at >= start_of_week,
                Order.created_at <= end_of_week
            ).all()
            
            total_orders = len(weekly_orders)
            total_revenue = sum(float(order.total_amount) for order in weekly_orders)
            
            # Payment breakdown
            cash_total = sum(float(order.total_amount) for order in weekly_orders 
                           if order.payment_method == 'cash' and order.payment_status == 'paid')
            credit_total = sum(float(order.total_amount) for order in weekly_orders 
                             if order.payment_method == 'credit' and order.payment_status == 'paid')
            unpaid_total = sum(float(order.total_amount) for order in weekly_orders 
                             if order.payment_status == 'pending')
            
            # Customer metrics
            weekly_customers = User.query.filter(
                User.role == 'customer',
                User.created_at >= start_of_week,
                User.created_at <= end_of_week
            ).count()
            
            # Daily breakdown
            daily_breakdown = []
            for i in range(7):
                day = week_start + timedelta(days=i)
                day_start = datetime.combine(day, datetime.min.time())
                day_end = datetime.combine(day, datetime.max.time())
                
                day_orders = [o for o in weekly_orders if day_start <= o.created_at <= day_end]
                day_revenue = sum(float(o.total_amount) for o in day_orders)
                
                daily_breakdown.append({
                    'day': day.strftime('%A'),
                    'date': day.strftime('%Y-%m-%d'),
                    'orders': len(day_orders),
                    'revenue': day_revenue
                })
            
            return {
                'week_start': week_start.strftime('%Y-%m-%d'),
                'week_end': week_end.strftime('%Y-%m-%d'),
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'cash_total': cash_total,
                'credit_total': credit_total,
                'unpaid_total': unpaid_total,
                'weekly_customers': weekly_customers,
                'daily_breakdown': daily_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error generating weekly report data: {str(e)}")
            return {}
    
    def generate_financial_summary(self):
        """Generate current financial summary"""
        try:
            # All time totals
            all_orders = Order.query.all()
            total_cash = sum(float(order.total_amount) for order in all_orders 
                           if order.payment_method == 'cash' and order.payment_status == 'paid')
            total_credit = sum(float(order.total_amount) for order in all_orders 
                             if order.payment_method == 'credit' and order.payment_status == 'paid')
            total_unpaid = sum(float(order.total_amount) for order in all_orders 
                             if order.payment_status == 'pending')
            
            # Current month
            today = datetime.now()
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            monthly_orders = Order.query.filter(Order.created_at >= month_start).all()
            monthly_revenue = sum(float(order.total_amount) for order in monthly_orders)
            
            return {
                'total_cash': total_cash,
                'total_credit': total_credit,
                'total_unpaid': total_unpaid,
                'monthly_revenue': monthly_revenue,
                'total_orders': len(all_orders),
                'monthly_orders': len(monthly_orders)
            }
            
        except Exception as e:
            logger.error(f"Error generating financial summary: {str(e)}")
            return {}

# Global reporting service instance
reporting_service = ReportingService()

