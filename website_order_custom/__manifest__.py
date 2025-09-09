# -*- coding: utf-8 -*-
{
    'name': "website_order_custom",

    'description': """
        Website Order Confirmation Automatically
    """,

    'author': "Kareem Mostafa",
    'website': "https://www.linkedin.com/in/kareem-mustafa-87b760180/",

    'category': 'Uncategorized',
    'version': '17.0.1.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'website', 'website_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}

