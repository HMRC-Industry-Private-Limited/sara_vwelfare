# -*- coding: utf-8 -*-
from odoo import api, fields, models

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    # provider = fields.Selection(selection_add=[('paytabs', 'Paytabs')], ondelete={'paytabs': 'set default'})
    code = fields.Selection(selection_add=[('paytabs', 'paytabs')],
                            ondelete={'paytabs': 'set default'},
                            help="The technical code of this payment provider",
                            string="Code")
    paytabs_profile_id = fields.Integer(string='Profile Id', required_if_provider='paytabs', groups='base.group_user')
    server_key = fields.Char(required_if_provider='paytabs', groups='base.group_user')
    client_key = fields.Char(required_if_provider='paytabs', groups='base.group_user')

    @api.model
    def _get_paytabs_url(self, environment):
        return 'https://secure.paytabs.sa/payment/request'
        