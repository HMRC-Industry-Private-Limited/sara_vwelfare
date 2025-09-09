# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider

def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import ValidationError
    version_info = common.exp_version()
    server_serie = version_info.get("server_serie")
    if server_serie != "17.0":
        raise ValidationError(
            "Module support Odoo series 17.0 found {}.".format(server_serie)
        )


def post_init_hook(env):
	setup_provider(env, 'paytabs')

def uninstall_hook(env):
	reset_payment_provider(env, 'paytabs')

