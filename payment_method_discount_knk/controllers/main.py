from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal
import logging

_logger = logging.getLogger(__name__)


class DiscountPaymentPortal(portal.CustomerPortal):

    @http.route('/shop/payment/update_provider', type='json', auth='public', csrf=False, website=True)
    def update_payment_provider(self, **kwargs):
        _logger.info("Payment provider update called with kwargs: %s", kwargs)

        provider_code = kwargs.get('provider_id')
        values = {}
        PaymentProvider = request.env['payment.provider']
        payment_provider = PaymentProvider.sudo().search([('code', '=', provider_code)], limit=1)
        payment_method_discount_enabled = request.env['ir.config_parameter'].sudo().get_param(
            'payment_method_discount.enabled', default=False
        )
        if payment_method_discount_enabled:
            if not payment_provider:
                _logger.warning("Payment provider not found for code: %s", provider_code)
                return {
                    'success': False,
                    'error': 'Payment provider not found'
                }

            sale_order = request.website.sale_get_order()

            if not sale_order:
                _logger.warning("Sale order not found")
                return {
                    'success': False,
                    'error': 'Sale order not found'
                }
            sale_order.sudo().write({'payment_provider_id': payment_provider.id})
            sale_order.sudo()._onchange_payment_provider_id()
            sale_order.sudo().update_price()

            values['payment_method_discount_knk.total_update'] = request.env['ir.ui.view']._render_template(
                "payment_method_discount_knk.total_update",
                {
                    'payment_method_discount_enabled': payment_method_discount_enabled,
                    'website_sale_order': sale_order,
                }
            )

            return values
