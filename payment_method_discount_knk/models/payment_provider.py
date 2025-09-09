# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields


class PaymentProviderInherit(models.Model):
    _inherit = 'payment.provider'

    discount_applied = fields.Float(
        string='Discount applied (%)',
        help='The discount applied as a percentage of the payment amount.')

    discount_method = fields.Selection([('fix', 'Fixed'), ('percentage', 'Percentage')], 'Discount Type')
