# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>)

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang


class AccountMove(models.Model):
    _inherit = 'account.move'

    discount_method = fields.Selection([('fix', 'Fixed'), ('percentage', 'Percentage')], 'Discount Type')
    discount_fix = fields.Monetary('Discount Amount')
    discount_per = fields.Float('Discount Percentage')
    total_discount = fields.Monetary('Discount', store=True, readonly=True)

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        res = super(AccountMove, self)._compute_amount()
        for invoice in self:
            if invoice.move_type != 'in_invoice':

                total_untaxed, total_untaxed_currency = 0.0, 0.0
                total_tax, total_tax_currency = 0.0, 0.0
                total_residual, total_residual_currency = 0.0, 0.0
                value, total, total_currency = 0.0, 0.0, 0.0

                if invoice.discount_method == 'fix' and invoice.amount_total > 0.0:
                    invoice.write({'total_discount': invoice.discount_fix * -1, 'discount_per': 0.0})
                elif invoice.discount_method == 'percentage' and invoice.amount_total > 0.0:
                    invoice.write({'total_discount': (invoice.amount_untaxed * invoice.discount_per / 100) * -1, 'discount_fix': 0.0})
                else:
                    invoice.write({'total_discount': 0.0, 'discount_fix': 0.0, 'discount_per': 0.0})
                for line in invoice.line_ids:
                    if invoice.is_invoice(True):
                        # === Invoices ===
                        if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                            # Tax amount.
                            total_tax += line.balance
                            total_tax_currency += line.amount_currency
                            total += line.balance
                            total_currency += line.amount_currency
                        elif line.display_type in ('product', 'rounding'):
                            # Untaxed amount.
                            total_untaxed += line.balance
                            total_untaxed_currency += line.amount_currency
                            total += line.balance
                            total_currency += line.amount_currency
                            value += line.price_subtotal
                        elif line.display_type == 'payment_term':
                            # Residual amount.
                            total_residual += line.amount_residual
                            total_residual_currency += line.amount_residual_currency
                    else:
                        # === Miscellaneous journal entry ===
                        if line.debit:
                            total += line.balance
                            total_currency += line.amount_currency

                sign = invoice.direction_sign
                # invoice.amount_untaxed = sign * total_untaxed_currency
                invoice.amount_tax = sign * total_tax_currency
                invoice.amount_total = sign * total_currency
                invoice.amount_residual = (-sign * total_residual_currency)
                # +invoice.total_discount
                invoice.amount_untaxed_signed = -total_untaxed
                invoice.amount_tax_signed = -total_tax
                invoice.amount_total_signed = abs(total) if invoice.move_type == 'entry' else -total
                invoice.amount_residual_signed = total_residual
                invoice.amount_total_in_currency_signed = abs(invoice.amount_total) if invoice.move_type == 'entry' else -(sign * invoice.amount_total)
                invoice.amount_total += invoice.total_discount
                invoice.amount_untaxed_signed += invoice.total_discount
                # invoice.amount_total +=invoice.total_discount
                invoice.amount_total_signed += invoice.total_discount
                invoice.amount_residual += invoice.total_discount
                invoice.amount_residual_signed += invoice.total_discount
                # invoice.amount_residual = invoice.amount_total
                invoice.amount_residual_signed = invoice.amount_total_signed
        return res

    @api.depends(
        'invoice_line_ids.currency_rate',
        'invoice_line_ids.tax_base_amount',
        'invoice_line_ids.tax_line_id',
        'invoice_line_ids.price_total',
        'invoice_line_ids.price_subtotal',
        'invoice_payment_term_id',
        'partner_id',
        'currency_id',
    )
    def _compute_tax_totals(self):

        rem = super(AccountMove, self)._compute_tax_totals()
        for move in self:
            if move.amount_tax:
                order_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
                move.tax_totals.update({
                    'amount_untaxed': sum(order_lines.mapped('price_subtotal')) + move.total_discount,
                    'amount_total': sum(order_lines.mapped('price_total')) + move.total_discount,
                    'formatted_amount_total': formatLang(self.env, sum(order_lines.mapped('price_total')) + move.total_discount),
                    'formatted_amount_untaxed': formatLang(self.env, sum(order_lines.mapped('price_subtotal')) + move.total_discount),
                    'subtotals': [{
                        'name': 'Untaxed Amount',
                        'amount': sum(order_lines.mapped('price_subtotal')) + move.total_discount,
                        'formatted_amount': formatLang(self.env, sum(order_lines.mapped('price_subtotal')) + move.total_discount),
                    }]
                })

        return rem

    def action_register_payment(self):
        res = super(AccountMove, self).action_register_payment()
        if self.total_discount:
            return {
                'name': _('Register Payment'),
                'res_model': 'account.payment.register',
                'view_mode': 'form',
                'context': {
                    'active_model': 'account.move',
                    'default_active_ids': self.ids,
                    'default_amount': self.amount_residual,
                    'default_discount_applied': self.total_discount
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        return res

    def update_price(self):
        for rec in self:
            rec._compute_amount()
        return True


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Register Payment'

    discount_applied = fields.Float(string="Discount")

    @api.depends('can_edit_wizard', 'amount')
    def _compute_payment_difference(self):
        super()._compute_payment_difference()
        for wizard in self:
            if not self.discount_applied:
                if wizard.can_edit_wizard:
                    batch_result = wizard._get_batches()[0]
                    total_amount_residual_in_wizard_currency = wizard\
                        ._get_total_amount_in_wizard_currency_to_full_reconcile(batch_result, early_payment_discount=False)[0]
                    wizard.payment_difference = total_amount_residual_in_wizard_currency - wizard.amount
                else:
                    wizard.payment_difference = 0.0
            else:
                if wizard.can_edit_wizard:
                    batch_result = wizard._get_batches()[0]
                    total_amount_residual_in_wizard_currency = wizard\
                        ._get_total_amount_in_wizard_currency_to_full_reconcile(batch_result, early_payment_discount=False)[0]
                    wizard.payment_difference = total_amount_residual_in_wizard_currency - wizard.amount + self.discount_applied
                else:
                    wizard.payment_difference = 0.0
