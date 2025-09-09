# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

import logging
import json
import requests
from odoo.http import request
from odoo import models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TransactionPayTabs(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_processing_values(self, processing_values):
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code == 'paytabs' and self.operation == 'online_token':
            payload = self._paytabs_prepare_payment_payload(token=True)
            headers = {
                "authorization": self.provider_id.paytabs_client_secret,
                'Content-Type': 'application/json'
            }
            payment_intent = requests.post(
                url=self.provider_id.paytabs_url().get('pay_page_url'),
                headers=headers,
                data=json.dumps(payload)
            ).json()
            self.provider_reference = payment_intent.get('tran_ref')
            redirect_url = payment_intent.get('redirect_url')
            _logger.info(
                f"\n\n Payment Paytab Token Response: {payment_intent} \n\n"
            )
            return {'paytabs_redirect_url': redirect_url}
        return res

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'paytabs':
            return res

        paytabs_tx_values = self._paytabs_prepare_payment_payload(token=False)
        if self.tokenize:
            paytabs_tx_values.update({
                "tokenise": 2,
            })
        headers = {
            "authorization": self.provider_id.paytabs_client_secret,
            'Content-Type': 'application/json'
        }
        result = requests.post(
            url=self.provider_id.paytabs_url().get('pay_page_url'),
            headers=headers,
            data=json.dumps(paytabs_tx_values)
        ).json()
        _logger.info(f"\n\n Paytab Payment Response = {result} \n\n")
        if result.get("tran_ref"):
            self.provider_reference = result["tran_ref"]
        else:
            raise ValidationError(_(result.get("message")))
        return {"paytabs_redirect_url": result.get("redirect_url") if result else False}

    def _create_paytabs_token_from_notification_data(self, data):
        token = self.env['payment.token'].sudo().create({
            'provider_id': self.provider_id.id,
            'payment_method_id': self.payment_method_id.id,
            'partner_id': self.partner_id.id,
            'provider_ref': self.provider_reference,
            "payment_details": data.get('payment_info').get("payment_description") if data.get('payment_info') else None,
            'paytabs_payment_method': data.get('token'),
        })
        self.write({
            'token_id': token.id,
            'tokenize': False,
        })
        _logger.info(
            "created token with id %(token_id)s for partner with id %(partner_id)s from "
            "transaction with reference %(ref)s",
            {
                'token_id': token.id,
                'partner_id': self.partner_id.id,
                'ref': self.reference,
            },
        )

    def _process_notification_data(self, data):
        res = super()._process_notification_data(data)
        if self.provider_code != 'paytabs':
            return res
        payment_data = data.get('payment_result')
        if payment_data.get("response_message") == 'Authorised' and payment_data.get("response_status") == "A":
            if self.tokenize and data.get('token', False):
                self._create_paytabs_token_from_notification_data(data)
            self._set_done()
        else:
            if payment_data.get("response_status") == "P" or payment_data.get('response_message') == "Pending":
                self._set_pending()
            elif payment_data.get("response_status") == "C" or payment_data.get("response_message") == "Cancelled":
                self._set_canceled()
            else:
                msg = payment_data.get("response_message", "Error")
                self._set_error(msg)

    def _paytabs_prepare_payment_payload(self, token):
        paytabs_payload = {
            "profile_id": self.provider_id.paytabs_client_id,
            "tran_type": "sale",
            "tran_class": "ecom",
            "cart_id": self.reference,
            "cart_currency": self.currency_id.name,
            "cart_amount": self.amount,
            "cart_description": self.reference,
            "paypage_lang": "en",
            "customer_details": {
                "name": self.partner_id.name,
                "email": self.partner_id.email,
                "phone": self.partner_id.phone,
                "street1": self.partner_id.street,
                "state": self.partner_id.state_id.name,
                "city": self.partner_id.city,
                "country": self.partner_id.country_id.code2,
                "zip": self.partner_id.zip,
                "ip": request.httprequest.environ['REMOTE_ADDR'],
            },
            "shipping_details": {
                "name": self.partner_id.name,
                "email": self.partner_id.email,
                "phone": self.partner_id.phone,
                "street1": self.partner_id.street,
                "state": self.partner_id.state_id.name,
                "city": self.partner_id.city,
                "country": self.partner_id.country_id.code2,
                "zip": self.partner_id.zip,
                "ip": request.httprequest.environ['REMOTE_ADDR'],
            },
            "return": self.provider_id._get_paytabs_url() + "?tran_ref=%s" % self.reference,
        }
        if token:
            paytabs_payload.update({
                "token": self.token_id.paytabs_payment_method,
                'tran_ref': self.reference,
            })
        else:
            paytabs_payload.update({
                "payment_methods": ["all"],
            })
        return paytabs_payload

    def _send_payment_request(self):
        super()._send_payment_request()
        if self.provider_code != 'paytabs':
            return

        if not self.token_id:
            raise ValidationError(
                _("Paytabs: The transaction is not linked to a token.")
            )
