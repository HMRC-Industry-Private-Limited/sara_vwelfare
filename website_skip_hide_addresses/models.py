# coding: utf-8

from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    always_skip_address = fields.Boolean(default=True)

    def _get_checkout_step_list(self):
        steps = super()._get_checkout_step_list()
        # Delivery step is always the second step
        if self.always_skip_address:
            steps.pop(1)
        return steps


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    always_skip_address = fields.Boolean(
        related='website_id.always_skip_address',
        readonly=False,
    )


