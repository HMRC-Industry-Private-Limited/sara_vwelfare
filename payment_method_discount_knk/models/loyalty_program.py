# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields


class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    payment_provider_id = fields.Many2one('payment.provider', string='Payment Provider', domain=[('state', 'in', ['enabled', 'test'])])
