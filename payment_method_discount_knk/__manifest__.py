# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': "Discount on Payment Methods",
    'version': '17.0.1.3',
    'summary': "'Discount on different Payment Methods' Apply discount on different payment. | Website Sale Payment Method Discount | Discount on payment method | payment method discount | Discount on payment provider | payment provider discount | Discount on payment terms | payment terms discount | discount payment | payment discount | discount payment provider | website Discount on payment method | website Discount on payment provider | website order discount on Payment Methods",
    'description': """
    Provide different discount over the payment methods like creditcard, debitcard etc.
    """,
    'category': 'Accounting',
    'author': 'Kanak Infosystems LLP.',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.kanakinfosystems.com',
    'license': 'OPL-1',
    'depends': ['sale_management', 'website_sale', 'loyalty', 'payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_provider.xml',
        'views/res_config_settings_views.xml',
        'views/account_payment_register_view.xml',
        'views/loyalty_program_view.xml',
        'views/sale_order_view.xml',
        'views/website_total_template_inherit.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_method_discount_knk/static/src/custom.js',
        ],
    },
    'price': 60,
    'application': True,
    'installable': True,
}
