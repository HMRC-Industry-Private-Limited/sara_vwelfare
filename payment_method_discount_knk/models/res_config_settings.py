# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_method_discount = fields.Boolean(
        string="Enable Payment Method Discount",
        help="Enable the option to apply discounts based on payment methods.", config_parameter='payment_method_discount.enabled'
    )

    payment_discount_account_id = fields.Many2one(
        'account.account',
        string='Discount Account',
        config_parameter='payment_method_discount.default_discount_account'
    )
