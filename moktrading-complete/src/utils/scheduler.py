#!/usr/bin/env python3

import schedule
import time
import threading
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from src.models.unified_models import db, Order, User, Product, OrderItem
from src.utils.notifications import notification_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportScheduler:
    """Automated report scheduler for daily, weekly, and monthly sales reports"""
    
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.scheduler_thread = None
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
    
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.running:
            logger.info("Scheduler is already running")
            return
        
        self.running = True
        
        # Schedule daily report at 11:59 PM
        schedule.every().day.at("23:59").do(self._run_daily_report)
        
        # Schedule weekly report on Sunday at 11:59 PM
        schedule.every().sunday.at("23:59").do(self._run_weekly_report)
        
        # Schedule monthly report on the last day of month at 11:59 PM
        schedule.every().day.at("23:59").do(self._check_monthly_report)
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("📅 Report scheduler started successfully")
        logger.info("📊 Daily reports: 11:59 PM every day")
        logger.info("📈 Weekly reports: 11:59 PM every Sunday")
        logger.info("📋 Monthly reports: 11:59 PM on last day of month")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("📅 Report scheduler stopped")
    
    def _run_scheduler(self):
        """Background scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)
    
    def _run_daily_report(self):
        """Generate and send daily report"""
        try:
            with self.app.app_context():
                logger.info("📊 Generating daily sales report...")
                report_data = self.generate_daily_report()
                success = notification_service.send_daily_report(report_data)
                
                if success:
                    logger.info("✅ Daily report sent successfully")
                else:
                    logger.error("❌ Failed to send daily report")
                    
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
    
    def _run_weekly_report(self):
        """Generate and send weekly report"""
        try:
            with self.app.app_context():
                logger.info("📈 Generating weekly sales report...")
                report_data = self.generate_weekly_report()
                success = notification_service.send_weekly_report(report_data)
                
                if success:
                    logger.info("✅ Weekly report sent successfully")
                else:
                    logger.error("❌ Failed to send weekly report")
                    
        except Exception as e:
            logger.error(f"Error generating weekly report: {str(e)}")
    
    def _check_monthly_report(self):
        """Check if today is the last day of month and send monthly report"""
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            # Check if tomorrow is a different month (today is last day of month)
            if tomorrow.month != today.month:
                with self.app.app_context():
                    logger.info("📋 Generating monthly sales report...")
                    report_data = self.generate_monthly_report()
                    success = notification_service.send_monthly_report(report_data)
                    
                    if success:
                        logger.info("✅ Monthly report sent successfully")
                    else:
                        logger.error("❌ Failed to send monthly report")
                        
        except Exception as e:
            logger.error(f"Error generating monthly report: {str(e)}")
    
    def generate_daily_report(self):
        """Generate daily sales report data"""
        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            # Get today's orders
            daily_orders = Order.query.filter(
                and_(Order.created_at >= start_of_day, Order.created_at <= end_of_day)
            ).all()
            
            # Calculate totals
            total_orders = len(daily_orders)
            total_revenue = sum(order.total_amount for order in daily_orders)
            cash_payments = sum(order.total_amount for order in daily_orders if order.payment_method == 'cash')
            credit_payments = sum(order.total_amount for order in daily_orders if order.payment_method in ['card', 'credit'])
            pending_payments = sum(order.total_amount for order in daily_orders if order.payment_status == 'pending')
            
            # Order status counts
            completed_orders = len([o for o in daily_orders if o.status == 'completed'])
            processing_orders = len([o for o in daily_orders if o.status == 'processing'])
            pending_orders = len([o for o in daily_orders if o.status == 'pending'])
            
            # New customers today
            new_customers = User.query.filter(
                and_(
                    User.created_at >= start_of_day,
                    User.created_at <= end_of_day,
                    User.is_admin == False
                )
            ).count()
            
            # Top products
            top_products = self._get_top_products_daily(daily_orders)
            
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
                'top_products_text': top_products,
                'active_carts': 0  # Could implement cart tracking
            }
            
        except Exception as e:
            logger.error(f"Error generating daily report data: {str(e)}")
            return {}
    
    def generate_weekly_report(self):
        """Generate weekly sales report data"""
        try:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())  # Monday
            week_end = week_start + timedelta(days=6)  # Sunday
            
            start_datetime = datetime.combine(week_start, datetime.min.time())
            end_datetime = datetime.combine(week_end, datetime.max.time())
            
            # Get week's orders
            weekly_orders = Order.query.filter(
                and_(Order.created_at >= start_datetime, Order.created_at <= end_datetime)
            ).all()
            
            # Calculate totals
            total_orders = len(weekly_orders)
            total_revenue = sum(order.total_amount for order in weekly_orders)
            cash_total = sum(order.total_amount for order in weekly_orders if order.payment_method == 'cash')
            credit_total = sum(order.total_amount for order in weekly_orders if order.payment_method in ['card', 'credit'])
            unpaid_total = sum(order.total_amount for order in weekly_orders if order.payment_status != 'paid')
            
            # New customers this week
            weekly_customers = User.query.filter(
                and_(
                    User.created_at >= start_datetime,
                    User.created_at <= end_datetime,
                    User.is_admin == False
                )
            ).count()
            
            # Daily breakdown
            daily_breakdown = []
            for i in range(7):
                day = week_start + timedelta(days=i)
                day_start = datetime.combine(day, datetime.min.time())
                day_end = datetime.combine(day, datetime.max.time())
                
                day_orders = [o for o in weekly_orders if day_start <= o.created_at <= day_end]
                day_revenue = sum(o.total_amount for o in day_orders)
                
                daily_breakdown.append({
                    'day': day.strftime('%A'),
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
    
    def generate_monthly_report(self):
        """Generate monthly sales report data"""
        try:
            today = datetime.now().date()
            month_start = today.replace(day=1)
            
            # Get next month's first day, then subtract 1 day to get last day of current month
            if today.month == 12:
                next_month = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month + 1, day=1)
            month_end = next_month - timedelta(days=1)
            
            start_datetime = datetime.combine(month_start, datetime.min.time())
            end_datetime = datetime.combine(month_end, datetime.max.time())
            
            # Get month's orders
            monthly_orders = Order.query.filter(
                and_(Order.created_at >= start_datetime, Order.created_at <= end_datetime)
            ).all()
            
            # Calculate totals
            total_orders = len(monthly_orders)
            total_revenue = sum(order.total_amount for order in monthly_orders)
            cash_total = sum(order.total_amount for order in monthly_orders if order.payment_method == 'cash')
            credit_total = sum(order.total_amount for order in monthly_orders if order.payment_method in ['card', 'credit'])
            unpaid_total = sum(order.total_amount for order in monthly_orders if order.payment_status != 'paid')
            
            # New customers this month
            monthly_customers = User.query.filter(
                and_(
                    User.created_at >= start_datetime,
                    User.created_at <= end_datetime,
                    User.is_admin == False
                )
            ).count()
            
            # Weekly breakdown
            weekly_breakdown = []
            current_week_start = month_start
            week_num = 1
            
            while current_week_start <= month_end:
                week_end_date = min(current_week_start + timedelta(days=6), month_end)
                week_start_dt = datetime.combine(current_week_start, datetime.min.time())
                week_end_dt = datetime.combine(week_end_date, datetime.max.time())
                
                week_orders = [o for o in monthly_orders if week_start_dt <= o.created_at <= week_end_dt]
                week_revenue = sum(o.total_amount for o in week_orders)
                
                weekly_breakdown.append({
                    'week': f'Week {week_num}',
                    'dates': f'{current_week_start.strftime("%m/%d")} - {week_end_date.strftime("%m/%d")}',
                    'orders': len(week_orders),
                    'revenue': week_revenue
                })
                
                current_week_start = week_end_date + timedelta(days=1)
                week_num += 1
            
            return {
                'month_name': month_start.strftime('%B %Y'),
                'month_start': month_start.strftime('%Y-%m-%d'),
                'month_end': month_end.strftime('%Y-%m-%d'),
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'cash_total': cash_total,
                'credit_total': credit_total,
                'unpaid_total': unpaid_total,
                'monthly_customers': monthly_customers,
                'weekly_breakdown': weekly_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error generating monthly report data: {str(e)}")
            return {}
    
    def _get_top_products_daily(self, orders):
        """Get top selling products for daily report"""
        try:
            product_sales = {}
            
            for order in orders:
                for item in order.items:
                    product_name = item.product.name
                    if product_name in product_sales:
                        product_sales[product_name] += item.quantity
                    else:
                        product_sales[product_name] = item.quantity
            
            if not product_sales:
                return "No sales today"
            
            # Sort by quantity sold
            sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
            
            # Format top 3 products
            top_products = []
            for i, (product, qty) in enumerate(sorted_products[:3]):
                top_products.append(f"{i+1}. {product} ({qty} sold)")
            
            return "\\n".join(top_products)
            
        except Exception as e:
            logger.error(f"Error getting top products: {str(e)}")
            return "Error calculating top products"
    
    def send_test_reports(self):
        """Send test reports immediately for testing"""
        try:
            with self.app.app_context():
                logger.info("🧪 Sending test reports...")
                
                # Send daily report
                daily_data = self.generate_daily_report()
                daily_success = notification_service.send_daily_report(daily_data)
                
                # Send weekly report
                weekly_data = self.generate_weekly_report()
                weekly_success = notification_service.send_weekly_report(weekly_data)
                
                # Send monthly report
                monthly_data = self.generate_monthly_report()
                monthly_success = notification_service.send_monthly_report(monthly_data)
                
                return {
                    'daily_success': daily_success,
                    'weekly_success': weekly_success,
                    'monthly_success': monthly_success
                }
                
        except Exception as e:
            logger.error(f"Error sending test reports: {str(e)}")
            return {'error': str(e)}

# Global scheduler instance
report_scheduler = ReportScheduler()

