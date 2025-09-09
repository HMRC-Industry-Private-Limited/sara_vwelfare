from odoo import models, fields, api

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    patient_name = fields.Char(
        string="Patient Name",
        compute="_compute_patient_name",  
        store=True
    )

    @api.depends('user_id', 'partner_ids')
    def _compute_patient_name(self):
        for record in self:
            if record.partner_ids:
                attendees = record.partner_ids.mapped('name')
                organizer = record.user_id.name
                # إرجاع أول اسم مختلف عن المنظم
                record.patient_name = next((name for name in attendees if name != organizer), '')

