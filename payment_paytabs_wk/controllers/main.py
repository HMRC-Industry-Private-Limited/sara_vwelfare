# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

import logging
import json
import requests

from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaytabsController(http.Controller):

    @http.route(['/paytabs/feedback'], type='http', auth='public', website=True, csrf=False, save_session=True)
    def paytabs_feedback(self, **post):
        tx = request.env['payment.transaction'].sudo().search(
            [('reference', '=', post.get("tran_ref"))])
        if tx and tx.provider_reference:
            params = {
                "profile_id": int(tx.provider_id.paytabs_client_id),
                "tran_ref": tx.provider_reference
            }
            headers = {
                "authorization": tx.provider_id.paytabs_client_secret,
                'Content-Type': 'application/json'
            }
            request_params = requests.post(
                url=tx.provider_id.paytabs_url().get('verify_payment'),
                headers=headers,
                data=json.dumps(params)
            ).json()
            _logger.info(
                f"\n\n Verify Payment Paytabs API RESPONSE: {request_params} \n\n"
            )
        else:
            request_params = {
                'response_message': "Error",
            }
        tx.sudo()._handle_notification_data('paytabs', request_params)
        return request.redirect('/payment/status')
