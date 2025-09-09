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
import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('paytabs', 'paytabs')],
                            ondelete={'paytabs': 'set default'},
                            help="The technical code of this payment provider",
                            string="Code")
    profile_key = fields.Char(string='Profile ID', groups='base.group_user',
                              help="PayTabs profile id of the user")
    api_key = fields.Char(string='API Key', required_if_provider='paytabs',
                          groups='base.group_user', help="PayTabs Server key")
    domain = fields.Char(string='API Endpoint', help='API Endpoint of Paytabs')

    def _get_default_payment_method_id(self, code):
        self.ensure_one()
        if self.code != 'paytabs':
            return super()._get_default_payment_method_id(code)
        return self.env.ref('entrivis_payment_paytabs.account_payment_method_paytabs').id

    @api.model
    def _paytabs_make_request(self, url, data=None, method='POST'):
        self.ensure_one()
        data.pop('api_url')
        try:
            response = requests.request(
                method, url, json=data,
                headers={
                    "Authorization": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=60)
            response_content = response.json()
            if 'code' in response_content and response_content['code'] == 1:
                raise ValidationError(
                    _("PayTabs: Check Profile ID and API Key"))
            if 'code' in response_content and response_content['code'] == 206:
                raise ValidationError(_("PayTabs: Currency not available."))
            return response_content
        except requests.exceptions.RequestException:
            _logger.exception("Unable to communicate with Paytabs: %s", url)
            raise ValidationError(
                _("PayTabs: Could not establish a connection to the API."))
