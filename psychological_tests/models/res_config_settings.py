# models/res_config_settings.py

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_for_public = fields.Boolean(
            string="Show pages for Visitors (Guests)",
            config_parameter='psychological_tests.show_for_public',
    )
    show_for_loggedin = fields.Boolean(
            string="Show pages for Logged-in Users",
            config_parameter='psychological_tests.show_for_loggedin',
    )
