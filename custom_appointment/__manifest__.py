{
    'name': 'Custom Appointment',
    'version': '1.0',
    'category': 'Extra Tools',
    'summary': 'Custom Appointment Management',
    'description': """
        API endpoints for appointments
    """,
    'depends': ['base', 'calendar'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
} 