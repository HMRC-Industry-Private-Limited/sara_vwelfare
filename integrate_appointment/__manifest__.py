{
    'name': 'integrate Appointments',
    'version': '17.0.0.1.0',
    'category': 'Services/Calendar',
    'summary': 'API endpoints ',
    'description': """
        API endpoints for appointments
    """,
    'depends': ['base', 'calendar', 'appointment'],
    'data': [
        'data/cron.xml',
        'views/doctor_views.xml',
        'views/patient_views.xml',
      #  'views/appointment_type.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
} 