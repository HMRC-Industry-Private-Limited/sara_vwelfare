# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class AcquirerPayTabs(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('paytabs', 'PayTabs')],
        ondelete={'paytabs': 'set default'}
    )
    paytabs_client_id = fields.Integer(
        'Client Id',
        help='PayTabs Client Profile Id',
        required_if_provider='paytabs',
        groups='base.group_user'
    )
    paytabs_client_secret = fields.Char(
        'Secret API Key',
        help='PayTabs Client Secret API Key',
        required_if_provider='paytabs',
        groups='base.group_user'
    )
    paytabs_domain = fields.Char(
        'Client Domain',
        help="Client Domain Based On Signup Region",
        required_if_provider='paytabs',
        groups='base.group_user'
    )

    def _compute_feature_support_fields(self):
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'paytabs').update({
            'support_tokenization': True,
        })

    def paytabs_url(self):
        return {
            "pay_page_url": self.paytabs_domain + "/payment/request",
            "verify_payment": self.paytabs_domain + '/payment/query',
            "token": self.paytabs_domain + "/payment/token",
        }

    def _get_paytabs_url(self):
        try:
            website = self.env['website'].sudo().get_current_website()
            base_url = website.get_base_url()
        except:
            base_url = self.get_base_url()
        return base_url + '/paytabs/feedback'
