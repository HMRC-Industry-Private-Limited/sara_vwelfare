# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class SkipHideAddressController(WebsiteSale):
    @http.route(
        '/shop/checkout', type='http', methods=['GET'], auth='public', website=True, sitemap=False
    )
    def shop_checkout(self, try_skip_step=None, **query_params):
        # print(request.env['website'].get_current_website().always_skip_address)
        if request.website.always_skip_address: try_skip_step = 'true'
        return super().shop_checkout(try_skip_step=try_skip_step, **query_params)

    def can_skip_delivery_step(self, order_sudo, delivery_methods):
        if request.website.always_skip_address: return True
        return super().can_skip_delivery_step( order_sudo, delivery_methods)

    def _check_addresses(self, order_sudo):
        if not request.website.always_skip_address:
            return super()._check_addresses(order_sudo)