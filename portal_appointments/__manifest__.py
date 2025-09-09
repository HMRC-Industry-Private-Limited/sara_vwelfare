{
    'name': 'Portal Appointments',
    'version': '17.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Show appointments in customer portal',
    'description': """
        This module allows customers to view their appointments in the portal.
        Created by Ahmed El-Gendy
        Email: your.email@example.com
        Website: https://yourwebsite.com
    """,
    'author': 'Moaaz Gafar',
    'maintainer': 'Moaaz Gafar',
    'support': 'm.gafar2024@gmail.com',
    'images': ['static/description/banner.png'], 
    'depends': ['portal', 'calendar', 'website', 'sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 1,
}