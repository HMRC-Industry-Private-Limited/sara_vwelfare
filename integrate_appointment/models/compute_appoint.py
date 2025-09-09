from odoo import models, fields, api

class AppointmentType(models.Model):
    _inherit = 'appointment.type'

    duration_minutes = fields.Integer(
        string="Duration (Minutes)",
        compute="_compute_duration_minutes",
        store=True
    )

    doctor_ids = fields.Many2many(
        'res.users', 
        string="Doctors", 
        compute="_compute_doctor_ids", 
        store=True,
        relation='appointment_type_doctor_rel',
    )

    @api.depends('appointment_duration')
    def _compute_duration_minutes(self):
        for record in self:
            record.duration_minutes = int(record.appointment_duration * 60) if record.appointment_duration else 0

    @api.depends('staff_user_ids')
    def _compute_doctor_ids(self):
        for record in self:
            if record.staff_user_ids:
                # نستخدم staff_user_ids مباشرة لأنها تحتوي على معرفات المستخدمين
                record.doctor_ids = [(6, 0, record.staff_user_ids.ids)]
            else:
                record.doctor_ids = [(5,)]  # إزالة أي قيم سابقة إذا لم يكن هناك staff_user_ids
