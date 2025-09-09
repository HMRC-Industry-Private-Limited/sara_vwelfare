# -*- coding: utf-8 -*-
# Part of Warlock Technologies Pvt. Ltd. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'PayTabs Payment Provider',
    'version':'17.0.0.2',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Payment Acquirer: PayTabs Implementation',
    'description': 'PayTabs Payment Acquirer',
    'author': 'Warlock Technologies Pvt Ltd.',
    'website': 'https://www.warlocktechnologies.com',
    "support": "support@warlocktechnologies.com",
    'depends':['payment', 'account', 'website_sale'],
    'data': [
        'views/payment_views.xml',
        'views/payment_paytabs_template.xml',
        # 'data/payment_method.xml',
        'data/payment_provider.xml',
    ],
    "images": ["images/payment_paytabs.png"],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    "price": 50,
    "currency": "USD",
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
