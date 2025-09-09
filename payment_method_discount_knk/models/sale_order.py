# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields, api
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_provider_id = fields.Many2one('payment.provider', string='Payment Provider', domain=[('state', 'in', ['enabled', 'test'])])
    discount_method = fields.Selection([('fix', 'Fixed'), ('percentage', 'Percentage')], 'Discount Type')
    discount_fix = fields.Monetary('Discount Amount')
    discount_per = fields.Float('Discount Percentage')
    total_discount = fields.Monetary('Discount', store=True, readonly=True)

    @api.onchange('payment_provider_id')
    def _onchange_payment_provider_id(self):
        if self.payment_provider_id:
            provider = self.payment_provider_id
            self.discount_method = provider.discount_method
            if provider.discount_method == 'fix':
                self.discount_fix = provider.discount_applied
                self.discount_per = 0.0
            elif provider.discount_method == 'percentage':
                self.discount_per = provider.discount_applied
                self.discount_fix = 0.0
        else:
            self.discount_method = False
            self.discount_fix = 0.0
            self.discount_per = 0.0

    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total')
    def _compute_amounts(self):
        res = super(SaleOrder, self)._compute_amounts()
        for order in self:
            if order.discount_method == 'fix' and order.amount_total > 0.0:
                order.write({'total_discount': order.discount_fix * -1, 'discount_per': 0.0})
            elif order.discount_method == 'percentage' and order.amount_total > 0.0:
                order.write({'total_discount': (order.amount_untaxed * order.discount_per / 100) * -1, 'discount_fix': 0.0})
            else:
                order.write({'total_discount': 0.0, 'discount_fix': 0.0, 'discount_per': 0.0})
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            order.amount_untaxed = sum(order_lines.mapped('price_subtotal')) + order.total_discount
            order.amount_total = sum(order_lines.mapped('price_total')) + order.total_discount
            order.amount_tax = sum(order_lines.mapped('price_tax'))
        return res

    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals(self):
        rem = super(SaleOrder, self)._compute_tax_totals()
        for order in self:
            if order.total_discount:
                order_lines = order.order_line.filtered(lambda x: not x.display_type)
                order.tax_totals.update({
                    'amount_untaxed': sum(order_lines.mapped('price_subtotal')) + order.total_discount,
                    'amount_total': sum(order_lines.mapped('price_total')) + order.total_discount,
                    'formatted_amount_total': formatLang(self.env, sum(order_lines.mapped('price_total')) + order.total_discount),
                    'formatted_amount_untaxed': formatLang(self.env, sum(order_lines.mapped('price_subtotal')) + order.total_discount),
                    'subtotals': []
                })
        return rem

    def update_price(self):
        for rec in self:
            rec._compute_amounts()
        return True

    def _prepare_invoice(self):

        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['discount_method'] = self.discount_method
        invoice_vals['discount_fix'] = self.discount_fix
        invoice_vals['discount_per'] = self.discount_per
        invoice_vals['total_discount'] = -(self.total_discount)
        return invoice_vals

    def _get_program_domain(self):
        """
        Returns the base domain that all programs have to comply to.
        """
        self.ensure_one()
        today = fields.Date.context_today(self)
        return [('active', '=', True), ('sale_ok', '=', True),
                ('company_id', 'in', (self.company_id.id, False)),
                '|', ('pricelist_ids', '=', False), ('pricelist_ids', 'in', [self.pricelist_id.id]),
                '|', ('date_from', '=', False), ('date_from', '<=', today),
                '|', ('date_to', '=', False), ('date_to', '>=', today),
                '|', ('payment_provider_id', '=', False), ('payment_provider_id', '=', self.payment_provider_id.id)]
