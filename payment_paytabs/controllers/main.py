# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################
import logging
import pprint
from odoo import http, tools, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class paytabsController(http.Controller):
    _cancel_url = '/payment/paytabs/cancel'
    _exception_url = '/payment/paytabs/error'
    _return_url = '/payment/paytabs/return'
    _site_url = ""

    @http.route(
        [_return_url, _cancel_url, _exception_url], type='http', auth='public', methods=['POST', 'GET'], csrf=False,
        save_session=False
    )
    def paytabs_return(self, **post):
        _logger.info(" +++++++++++++++++++++ received PaytabsController return data +++++++++++++++++++++:\n%s",
                     pprint.pformat(post))
        data = self._normalize_data_keys(post)
        if data.get('respstatus') == 'A':
            pt_obj = request.env['payment.transaction'].sudo()
            tx_id = pt_obj.search([('paytab_trans', '=', data.get('tranref'))], limit=1)
            if tx_id:
                request.session['new_trans'] = [tx_id.id]
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            'paytabs', data
        )
        tx_sudo._handle_notification_data('paytabs', data)
        return request.redirect('/payment/status')

    @staticmethod
    def _normalize_data_keys(data):
        """ Set all keys of a dictionary to lower-case.

        As Paytabs parameters names are case insensitive, we can convert everything to lower-case
        to easily detected the presence of a parameter by checking the lower-case key only.

        :param dict data: The dictionary whose keys must be set to lower-case
        :return: A copy of the original data with all keys set to lower-case
        :rtype: dict
        """
        return {key.lower(): val for key, val in data.items()}
