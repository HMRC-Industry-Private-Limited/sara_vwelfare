##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2020-Today Entrivis Tech PVT. LTD. (<http://www.entrivistech.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
import logging
from werkzeug import urls
from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils
from odoo.addons.entrivis_payment_paytabs.controllers.main import PaymentPaytabs

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator='-',
                           **kwargs):
        if provider_code == 'paytabs':
            prefix = payment_utils.singularize_reference_prefix()
        return super()._compute_reference(provider_code, prefix=prefix,
                                          separator=separator, **kwargs)

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'paytabs':
            return res
        return self._paytabs_prepare_request_data()

    def _paytabs_prepare_request_data(self):
        api_url = self.env.ref('entrivis_payment_paytabs.payment_acquirer_paytabs').domain + f"/payment/request"
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        paytabs_values = {
            "profile_id": int(self.provider_id.profile_key),
            "tran_type": "sale",
            "tran_class": "ecom",
            "cart_description": self.reference,
            "cart_id": self.reference,
            "cart_currency": self.currency_id.name,
            "cart_amount": self.amount,
            'return': urls.url_join(base_url, PaymentPaytabs._return_url),
            'callback': urls.url_join(base_url, PaymentPaytabs._return_url),
            "api_url": api_url,
            "customer_details": {
                "name": self.partner_name or '',
                "email": self.partner_email or '',
                "street1": self.partner_address or '',
                "city": self.partner_city or '',
                "state": self.partner_state_id.code or '',
                "country": self.partner_country_id.code or '',
                "zip": self.partner_zip or ''
            },
        }
        order = False
        if 'sale_order_ids' in self.sudo()._fields:  # The module `sale` is installed.
            order = self.sudo().sale_order_ids[:1]
        if 'invoice_ids' in self.sudo()._fields:  # The module `Accounting` is installed.
            order = self.sudo().invoice_ids[:1] or order
        if order:
            paytabs_values['shipping_details'] = {
                "name": order.partner_shipping_id.display_name or '',
                "email": order.partner_shipping_id.email or '',
                "street1": order.partner_shipping_id.street or '',
                "city": order.partner_shipping_id.city or '',
                "state": order.partner_shipping_id.state_id.code or '',
                "country": order.partner_shipping_id.country_id.code or '',
                "zip": order.partner_shipping_id.zip or ''
            }
        paytabs_values['return'] += f"?transaction_reference={self.id}"
        paytabs_values['callback'] += f"?transaction_reference={self.id}"
        response_content = self.provider_id._paytabs_make_request(
            api_url, paytabs_values)
        response_content['api_url'] = response_content.get('redirect_url')
        self.provider_reference = response_content.get('tran_ref')
        return response_content

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        if provider_code != 'paytabs':
            return tx
        reference = notification_data.get('cart_id', False)
        if not reference:
            raise ValidationError(_("PayTabs: No reference found."))
        tx = self.search(
            [('reference', '=', reference), ('provider_code', '=', 'paytabs')])
        if not tx:
            raise ValidationError(
                _("PayTabs: No transaction found matching reference"
                  "%s.") % reference)
        return tx

    def _handle_notification_data(self, provider_code, notification_data):
        tx = self._get_tx_from_notification_data(provider_code,
                                                 notification_data)
        tx._process_notification_data(notification_data)
        tx._execute_callback()
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'paytabs':
            return
        status = notification_data.get('payment_result').get('response_status')
        if status == 'A':
            self.with_user(SUPERUSER_ID)._set_done(state_message="Authorised")
        elif status == 'APPROVED':
            self.with_user(SUPERUSER_ID)._set_pending(state_message="Authorised but on hold for "
                                                                    "further anti-fraud review")
        elif status in ('E', 'D'):
            self.with_user(SUPERUSER_ID)._set_canceled(state_message="Error")
        else:
            _logger.warning("Received unrecognized payment state %s for "
                            "transaction with reference %s",
                            status, self.reference)
            self.with_user(SUPERUSER_ID)._set_error("PayTabs: " + _("Invalid payment status."))
