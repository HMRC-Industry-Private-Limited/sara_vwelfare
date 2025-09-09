/** @odoo-module **/
import paymentForm from '@payment/js/payment_form';
import publicWidget from "@web/legacy/js/public/public_widget";

paymentForm.include({
    _onPaymentMethodChange(ev) {
        var $input = $(ev.currentTarget);
        var providerCode = $input.data('provider-code');
        if (providerCode) {
            return this.rpc("/shop/payment/update_provider", {
                'provider_id': providerCode,
            }).then((data) => {
                if (data) {
                    $("#cart_total").replaceWith(data['payment_method_discount_knk.total_update']);
                }
            });
        }
    },
    async _selectPaymentOption(ev) {
        var rec = this._super(...arguments);
        this._onPaymentMethodChange(ev);
        return rec
    }
});