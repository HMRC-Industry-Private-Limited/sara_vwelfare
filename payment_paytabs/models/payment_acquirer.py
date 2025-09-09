# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################
from urllib.parse import urlparse, urljoin
import logging
import json
from odoo.addons.payment_paytabs.controllers.main import paytabsController
from odoo import api, fields, models, _
from requests import Request, Session
from requests.adapters import HTTPAdapter
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PaymentAcquirerPayTabs(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('paytabs', 'Paytabs')], ondelete={'paytabs': 'set default'})
    merchant_id = fields.Char('Merchant ID', required_if_provider='paytabs')
    merchant_email = fields.Char('Merchant Email', required_if_provider='paytabs')
    secret_key = fields.Char('Secret Key', required_if_provider='paytabs')
    secret_hash = fields.Char('Client Key', required_if_provider='paytabs')
    api_endpoint = fields.Char(string='The API endpoint', required_if_provider='paytabs',
                               default='https://secure-global.paytabs.com/payment/request')


class TxPaytabs(models.Model):
    _inherit = 'payment.transaction'

    paytab_trans = fields.Char("Paytab Transaction")

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return paytabs-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of acquirer-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_id.code != 'paytabs':
            return res

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        if processing_values.get('currency_id'):
            currency_id = self.env['res.currency'].browse(processing_values['currency_id'])
        else:
            currency_id = self.env.company.currency_id
        customer_details = {}
        partner_id = self.env['res.partner'].browse(processing_values['partner_id'])

        customer_details.update({
            "name": partner_id.name or '',
            "email": partner_id.email or '',
            "street1": partner_id.street or '',
            "city": partner_id.city or '',
            "state": partner_id.state_id.code or '',
            "country": partner_id.country_id.code or '',
        })

        rendering_values = {
            "profile_id": str(self.provider_id.merchant_id),
            "tran_type": 'sale',
            "tran_class": 'ecom',
            "cart_description": "Order %s" % processing_values.get('reference', ''),
            "cart_id": "Order %s" % processing_values.get('reference', ''),
            "cart_currency": currency_id.name or '',
            "cart_amount": processing_values.get('amount', 0.0),
            "callback": '%s' % urljoin(base_url, paytabsController._return_url),
            "return": '%s' % urljoin(base_url, paytabsController._return_url),
            "redirect_url": "https://secure-global.paytabs.com/payment/page/REF/redirect",
            "customer_details": customer_details
        }

        _logger.info('-------------------------rendering_values : %s ' % rendering_values)

        full_api = self.provider_id.api_endpoint
        data = rendering_values

        session = Session()
        session.mount('http://', HTTPAdapter(max_retries=3))
        session.mount('https://', HTTPAdapter(max_retries=3))
        method = "POST"

        headers = {
            'Content-Type': 'application/json',
            'authorization': str(self.provider_id.secret_key)
        }

        request = Request(method, full_api, data=json.dumps(data), headers=headers)
        final_request = request.prepare()

        response = session.send(final_request, verify=True, proxies=dict(), timeout=500, allow_redirects=True)
        code = response.json()

        _logger.info('+++++++++++++++++++++Requested transaction +++++++++++++++++++++ : %s ' % code)
        tran_ref = code.get('tran_ref')

        if 'redirect_url' in code and code.get('redirect_url'):
            site_url = code['redirect_url']
            transaction_id = self.env['payment.transaction'].search(
                [('reference', '=', processing_values.get('reference', ''))], limit=1)
            transaction_id.write({'paytab_trans': tran_ref})
            rendering_values.update({'paytab_trans': tran_ref})
            rendering_values.update({'payment_url': site_url, 'api_url': site_url})
        else:
            raise ValidationError(
                "PayTab: " + _("Please Contact administrator")
            )

        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on paytabs data.
        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if inconsistent data were received
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'paytabs' or len(tx) == 1:
            return tx

        _logger.info('-------------------------data : %s ' % notification_data)
        reference = notification_data.get('tranref', False)

        if reference and (not tx):
            tx = self.search([('paytab_trans', '=', reference)], limit=1)

        if not tx:
            raise ValidationError(
                "Paytabs: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on paytabs data.

        Note: self.ensure_one()

        :param dict data: The feedback data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'paytabs':
            return

        _logger.info('-------------------------data : %s ' % notification_data)
        status_code = notification_data.get('respstatus', 'A')

        if status_code == 'A':
            self._set_done()
        else:  # Error / Unknown code
            error_code = 'An error was encountered while processing the transaction. \
            	            Kindly contact PayTabs customer service for further clarification.'
            if notification_data.get('respMessage', False):
                error_code = notification_data['respMessage']
            _logger.info(
                "received data with invalid status code %s and error code %s",
                status_code, error_code
            )
            self._set_error(
                "Paytabs: " + _(
                    "Received data with status code \"%(status)s\" and error code \"%(error)s\"",
                    status=status_code, error=error_code
                )
            )
