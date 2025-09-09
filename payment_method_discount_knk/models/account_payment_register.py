# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, api, fields
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CustomAccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    original_amount = fields.Float(string='Original Amount', readonly=True)

    @api.onchange('payment_method_line_id')
    def _onchange_payment_method_line_id(self):
        if not self.payment_method_line_id:
            return
        is_discount_enabled = self.env['ir.config_parameter'].sudo().get_param('payment_method_discount.enabled')
        if not is_discount_enabled:
            self.amount = self.original_amount
            return
        provider = self.env['payment.provider'].search([('code', '=', self.payment_method_line_id.code)], limit=1)
        if not self.original_amount:
            self.original_amount = self.amount
        if provider:
            if self.payment_method_line_id.name != "manual":
                discount_percentage = provider.discount_applied or 0.0
                if discount_percentage > 0.0:
                    discount = self.original_amount * (discount_percentage / 100.0)
                    self.amount = self.original_amount - discount
                    self.payment_difference_handling = 'reconcile'
                    discount_account_id = self.env['ir.config_parameter'].sudo().get_param(
                        'payment_method_discount.default_discount_account')
                    if discount_account_id:
                        writeoff_account = self.env['account.account'].browse(int(discount_account_id))
                        if writeoff_account.exists():
                            self.writeoff_account_id = writeoff_account.id
                            _logger.info("Set writeoff account: %s", writeoff_account.name)
                        else:
                            raise UserError("Discount account not found. Please configure it in Settings.")
                    else:
                        raise UserError("Please configure the discount account in Settings.")
                else:
                    self.amount = self.original_amount
        else:
            self.amount = self.original_amount
