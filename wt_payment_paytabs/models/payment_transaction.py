# -*- coding: utf-8 -*-
import base64
import json
import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils


import logging
_logger = logging.getLogger(__name__)

class PaymentToken(models.Model):
    _inherit = 'payment.token'

    paytabs_token = fields.Char()


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # @api.model
    # def _get_tx_from_feedback_data(self, provider_code, data):
    #     tx = super()._get_tx_from_feedback_data(provider_code, data)
    #     if provider_code != 'paytabs':
    #         return tx

    #     # data = self._sips_data_to_object(data['Data'])
    #     reference = data.get('cartId')

    #     if reference:
    #         tx = self.search([('reference', '=', reference)], limit=1)

    #     if not tx:
    #         raise ValidationError(
    #             "PayTabs: " + _("No transaction found matching reference %s.", reference)
    #         )
    #     return tx


    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Get payment status from Paytabs.

        :param provider_code: The code of the provider handling the transaction.
        :param notification_data: The data received from Paytabs notification.
        :return: The transaction matching the reference.
        """
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        if provider_code != 'paytabs':
            return tx

        # data = self._sips_data_to_object(data['Data'])
        reference = notification_data.get('cartId')

        if reference:
            tx = self.search([('reference', '=', reference)], limit=1)

        if not tx:
            raise ValidationError(
                "PayTabs: " + _("No transaction found matching reference %s.", reference)
            )
        return tx


    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return saferpay-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of acquirer-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'paytabs':
            return res

        address = []
        for partner in [self.partner_id, self.sale_order_ids.partner_shipping_id]:
            address.append({"name": partner.name,
                "email": partner.email or '',
                "phone": partner.phone or '',
                "street1": partner.street or '',
                "city": partner.city or '',
                "state": partner.state_id.code or '',
                "country": partner.country_id.code or '',
                "zip": partner.zip or ''
                })
        base_url = self.get_base_url()
        data = {"profile_id": self.provider_id.paytabs_profile_id,
            "tran_type": "sale",
            "tran_class": "ecom",
            "cart_id": self.reference,
            "cart_currency": "SAR",
            "cart_amount": self.amount,
            "cart_description": "Description of the items/services",
            "paypage_lang": "en",
            "callback": base_url + "/paytabs/payment/callback",
            "return": base_url + "/paytabs/payment/validate",
            "customer_details": address[0],
            "shipping_details": address[1]
            }

        # if self.tokenize and not self.token_id:
        #     data.update({'tokenise': 2})
        data = json.dumps(data)
        url = self.provider_id._get_paytabs_url('environment')
        headers = {'authorization': self.provider_id.server_key,
        'content-type': 'application/json'}
        response = requests.request('POST', url, headers=headers, data=data)
        if response.status_code == 200:
            res = response.json()
            return {'api_url': res.get('redirect_url')}
        return processing_values

    # def _process_feedback_data(self, data):
    #     """ Override of payment to process the transaction based on Sips data.

    #     Note: self.ensure_one()

    #     :param dict data: The feedback data sent by the provider
    #     :return: None
    #     """
    #     super()._process_feedback_data(data)
    #     if self.provider_code != 'paytabs':
    #         return

    #     self.acquirer_reference = data.get('tranRef')
    #     status_code = data.get('respStatus')
    #     if status_code == 'A':
    #         self._set_done()
    #         # if self.tokenize and not self.token_id:
    #         #     self._paytabs_tokenize_from_feedback_data(data)
    #     elif status_code == 'D':
    #         self._set_canceled()
    #     elif status_code in ['P', 'H']:  # Held for Review
    #         self._set_pending()
    #     else:  # Error / Unknown code
    #         error_code = data.get('respCode')
    #         _logger.info(
    #             "received data with invalid status code %s and error code %s",
    #             status_code, error_code
    #         )
    #         self._set_error(
    #             "PayTabs: " + _(
    #                 "Received data with status code \"%(status)s\" and error code \"%(error)s\"",
    #                 status=status_code, error=error_code
    #             )
    #         )


    def _process_notification_data(self, notification_data):
        """
        Process the notification data received from PayTabs.

        This method processes the notification data and updates the payment
        state of the transaction accordingly.

        :param notification_data: The data received from PayTabs notification.
            """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'paytabs':
            return

        status = notification_data.get('respStatus')
        if status == 'A':
            self._set_done(state_message="Authorised")
        elif status == 'APPROVED':
            self._set_pending(state_message="Authorised but on hold for "
                                            "further anti-fraud review")
        elif status in ('E', 'D'):
            self._set_canceled(state_message="Error")
        else:
            _logger.warning("Received unrecognized payment state %s for "
                            "transaction with reference %s",
                            status, self.reference)
            self._set_error("PayTabs: " + _("Invalid payment status."))





    def _paytabs_tokenize_from_feedback_data(self, data):
        """ Create a token from feedback data.

        :param dict data: The feedback data sent by the provider
        :return: None
        """
        res = self._paytabs_query_token(data)
        if res:
            token = self.env['payment.token'].create({
                'provider_id': self.provider_id.id,
                'name': res.get('payment_info', {}).get('payment_description'),
                'partner_id': self.partner_id.id,
                'acquirer_ref': data.get('tranRef'),
                'paytabs_token': data.get('token'),
                'verified': True,  # The payment is authorized, so the payment method is valid
            })
            self.write({
                'token_id': token.id,
                'tokenize': False,
            })
            _logger.info(
                "created token with id %s for partner with id %s", token.id, self.partner_id.id
            )

    def _paytabs_query_token(self, data):
        url = 'https://secure.paytabs.sa/payment/token'
        headers = {'authorization': self.provider_id.server_key,
        'content-type': 'application/json'}
        data = json.dumps({'profile_id': self.provider_id.paytabs_profile_id,
            'token': data.get('token')})
        response = requests.request('POST', url, headers=headers, data=data)
        if response.status_code == 200:
            res = response.json()
            return res
        return False

    def _send_payment_request(self):
        super()._send_payment_request()
        if self.provider_code != 'paytabs':
            return
        base_url = self.get_base_url()
        data = json.dumps({"profile_id": self.provider_id.paytabs_profile_id,
            "tran_type": "sale",
            "tran_class": "recurring",
            "cart_id": self.reference,
            "cart_currency": "SAR",
            "cart_amount": self.amount,
            "cart_description": "Description of the items/services",
            "token": self.token_id.paytabs_token,
            "tran_ref": self.token_id.acquirer_ref,
            "callback": base_url + "/paytabs/payment/validate"
        })
        headers = {'authorization': self.provider_id.server_key}
        url = self.provider_id._get_paytabs_url('environment')
        response = requests.request('POST', url, headers=headers, data=data)
        if response.status_code == 200:
            res = response.json()
            self._handle_feedback_data('paytabs', res)

        # if not self.token_id.authorize_profile:
        #     raise UserError("Authorize.Net: " + _("The transaction is not linked to a token."))

        # authorize_API = AuthorizeAPI(self.acquirer_id)
        # if self.acquirer_id.capture_manually:
        #     res_content = authorize_API.authorize(self, token=self.token_id)
        #     _logger.info("authorize request response:\n%s", pprint.pformat(res_content))
        # else:
        #     res_content = authorize_API.auth_and_capture(self, token=self.token_id)
        #     _logger.info("auth_and_capture request response:\n%s", pprint.pformat(res_content))

        # # As the API has no redirection flow, we always know the reference of the transaction.
        # # Still, we prefer to simulate the matching of the transaction by crafting dummy feedback
        # # data in order to go through the centralized `_handle_feedback_data` method.
        # feedback_data = {'reference': self.reference, 'response': res_content}


