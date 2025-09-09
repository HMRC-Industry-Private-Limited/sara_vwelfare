import logging
from odoo import http
from odoo.http import request
import requests
import werkzeug
from werkzeug import urls
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)

class PayTabsController(http.Controller):

    _return_url = '/paytabs/payment/validate'
    # _notify_url = '/paytabs/payment/notify'

    @http.route(_return_url, type='http', auth="public", methods=['POST','GET'], csrf=False, save_session=False)    
    def paytabs_validate(self, **post):
        try:
            request.env['payment.transaction'].sudo()._get_tx_from_notification_data('paytabs', post)
        except ValidationError:
            pass
        request.env['payment.transaction'].sudo()._handle_notification_data('paytabs', post)
        return request.redirect('/payment/status')
        
    

    # _return_url = '/payment/paytabs/return'

    # @http.route(_return_url, type='http', auth='public',
    #             methods=['POST'], csrf=False, save_session=False)
    # def paytabs_return(self, **post):
    #     """
    #     Handle the return from PayTabs payment gateway.

    #     This method is used when PayTabs sends a notification with payment
    #     data. It retrieves the transaction data, handles the notification
    #     data, and redirects the user to the payment status page.

    #     :param post: The POST data received from PayTabs.
    #     :return: A redirect response to the payment status page.
    #     """
    #     tx_sudo = request.env[
    #         'payment.transaction'].sudo()._handle_feedback_data(
    #         'paytabs', post)
    #     tx_sudo._handle_notification_data('paytabs', post)
    #     return request.redirect('/payment/status')
