from odoo import fields, models

class InheritedAppointmentType(models.Model):
    _name = 'appointment.type'
    _inherit = 'appointment.type'
    _description = 'Inherited Appointment Type'

    staff_user_ids = fields.Many2many(
        'res.users', 
        string='Users',  
        domain=['|', ('share', '=', False), ('share', '=', True)],
        required=True,  
        index=True,  
        copied=True  
    )