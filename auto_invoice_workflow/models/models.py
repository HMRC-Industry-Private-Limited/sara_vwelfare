from odoo import models, api, _
from datetime import timedelta
from odoo.fields import Datetime
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if res and res.team_id and 'ecommerce' in res.team_id.name.lower():
            res.action_confirm()
        return res

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.state == 'sale':
                for line in order.order_line:
                    if line.product_id.type == 'service' and line.product_id.product_tmpl_id.booking_fees:
                        appointment_start = line.appointment_start or Datetime.now()
                        appointment_end = line.appointment_end or (Datetime.now() + timedelta(hours=1))

                        # Create calendar event
                        event_vals = {
                            'name': f"Appointment: {line.name}",
                            'start': appointment_start,
                            'stop': appointment_end,
                            'user_id': line.product_id.appointment_resource_id.user_id.id or order.user_id.id,
                            'partner_id': order.partner_id.id,
                            'state': 'confirmed',
                            'description': f"Order: {order.name}\nService: {line.name}\nCustomer: {order.partner_id.name}",
                            'privacy': 'public',
                            'show_as': 'busy',
                            'allday': False,
                        }

                        event = self.env['calendar.event'].create(event_vals)
                         # Add customer as attendee
                        if order.partner_id and order.partner_id.email:
                            try:
                                self.env['calendar.attendee'].create({
                                    'event_id': event.id,
                                    'partner_id': order.partner_id.id,
                                    'state': 'accepted',
                                })
                            except Exception as e:
                                _logger.warning(f"Could not add attendee to calendar event: {e}")

                        # Post message in order
                        order.message_post(
                            body=f"""
                            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 10px 0;">
                                <h4 style="color: #2d5f3f;">✅ Appointment Confirmed!</h4>
                                <p><strong>Service:</strong> {line.name}</p>
                                <p><strong>Date:</strong> {appointment_start.strftime('%A, %B %d, %Y')}</p>
                                <p><strong>Time:</strong> {appointment_start.strftime('%I:%M %p')} - {appointment_end.strftime('%I:%M %p')}</p>
                                <p><strong>Duration:</strong> {(appointment_end - appointment_start).total_seconds() / 3600:.1f} hours</p>
                                <p style="margin-top: 10px;">
                                    <a href="/my/appointments" style="color: #2d5f3f; text-decoration: underline;">
                                        View all your appointments →
                                    </a>
                                </p>
                            </div>
                            """,
                            subject="🗓️ Appointment Confirmed",
                            message_type='comment',
                            subtype_xmlid='mail.mt_comment'
                        )
                         # Send email notification
                        self._send_appointment_email(order, line, event)

                order._create_invoices()
        return res
    def _send_appointment_email(self, order, line, event):
        """Send appointment confirmation email"""
        if not order.partner_id.email:
            return

        try:
            mail_template = self.env['mail.template'].create({
                'name': 'Appointment Confirmation',
                'model_id': self.env.ref('sale.model_sale_order').id,
                'subject': f'Appointment Confirmation - {line.name}',
                'body_html': f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h2 style="color: #2E86AB; margin-bottom: 10px;">Appointment Confirmed! ✅</h2>
                        </div>

                        <p>Dear {order.partner_id.name},</p>
                        <p>Your appointment has been successfully confirmed:</p>

                        <div style="background-color: #f8f9fa; padding: 25px; border-radius: 10px; margin: 25px 0;">
                            <h3 style="color: #2E86AB; margin-top: 0;">Appointment Details</h3>
                            <p><strong>Service:</strong> {line.name}</p>
                            <p><strong>Date:</strong> {event.start.strftime('%A, %B %d, %Y')}</p>
                            <p><strong>Time:</strong> {event.start.strftime('%I:%M %p')} - {event.stop.strftime('%I:%M %p')}</p>
                            <p><strong>Order Number:</strong> {order.name}</p>
                        </div>

                        <p>Thank you for choosing our services!</p>

                        <div style="text-align: center; margin-top: 30px;">
                            <a href="/my/appointments" style="background-color: #2E86AB; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                                View My Appointments
                            </a>
                        </div>
                    </div>
                """,
                'auto_delete': False,
            })

            mail_template.send_mail(order.id, force_send=True)

        except Exception as e:
            _logger.warning(f"Failed to send appointment confirmation email: {e}")

    @api.multi  
    def _create_invoices(self):
        """Create invoices for confirmed orders"""
        for order in self:
            if not order.invoice_ids and order.state == 'sale':
                try:
                    invoice = order._create_invoices()
                    if invoice:
                        # Optionally auto-validate for appointment services
                        has_appointments = any(
                            line.product_id.type == 'service' and 
                            line.product_id.product_tmpl_id.booking_fees 
                            for line in order.order_line
                        )
                        if has_appointments:
                            invoice.action_post()
                except Exception as e:
                    _logger.warning(f"Failed to create invoice for order {order.name}: {e}")
        return True
