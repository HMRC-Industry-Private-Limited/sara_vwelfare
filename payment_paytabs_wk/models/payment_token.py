# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################

import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    paytabs_payment_method = fields.Char(
        string="Paytabs Payment Method ID",
        readonly=True
    )
