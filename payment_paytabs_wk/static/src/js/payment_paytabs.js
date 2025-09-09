/** @odoo-module **/

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import paymentForm from '@payment/js/payment_form';

paymentForm.include({
    _processTokenFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode === 'paytabs') {
            window.location = processingValues['paytabs_redirect_url'];
        }
        else {
            return this._super(...arguments);
        }
    }
});
