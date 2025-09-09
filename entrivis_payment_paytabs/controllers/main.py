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
from odoo import http
from odoo.http import request
import requests


class PaymentPaytabs(http.Controller):
    _return_url = '/payment/paytabs/return'

    @http.route(_return_url, type='http', auth="public", methods=['GET', 'POST'], csrf=False, website=True)
    def paytabs_return(self, transaction_reference, **post):
        api_url = request.env['payment.provider'].sudo().search(
            [('code', '=', 'paytabs')]).domain
        payment_transaction_rec = request.env['payment.transaction'].sudo().browse(int(transaction_reference))
        data = {
            "profile_id": int(payment_transaction_rec.provider_id.profile_key),
            "tran_ref": payment_transaction_rec.provider_reference,
        }
        response = requests.request(
            "POST", f"{api_url}/payment/query", json=data,
            headers={
                "Authorization": payment_transaction_rec.provider_id.api_key,
                "Content-Type": "application/json",
            },
        )
        response_content = response.json()
        payment_transaction_rec._handle_notification_data('paytabs', response_content)
        return request.redirect('/payment/status')
