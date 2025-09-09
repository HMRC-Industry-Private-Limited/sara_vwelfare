##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2020-Today Entrivis Tech PVT. LTD. (<http://www.entrivistech.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
{
    'name': 'PayTabs Payment Gateway Integration : Odoo',
    'version': '17.0.1.0.2',
    'category': 'Accounting/Payment Providers',
    'summary': 'Paytabs Payment Integration',
    'description': "This module enables seamless payments through PayTabs, "
                   "ensuring secure and convenient online transactions.",
    'author': 'Entrivis Tech Pvt. Ltd.',
    'website': 'https://www.entrivistech.com',
    'depends': ['payment'],
    'data': [
        'views/payment_provider_views.xml',
        'views/payment_paytabs_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': '25',
    'currency': 'EUR',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/entrivis-paytabs.png'],
}
