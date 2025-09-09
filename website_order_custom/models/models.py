# -*- coding: utf-8 -*-

from odoo import models, fields, api


class NewModule(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        order = super().create(vals_list)
        if order and order.websit_id:
            order.action_confirm()
        return order


