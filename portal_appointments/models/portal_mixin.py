from odoo import fields, models

class PortalMixin(models.AbstractModel):
    _inherit = 'portal.mixin'
    
    appointment_count = fields.Integer(compute='_compute_appointment_count')
    
    def _compute_appointment_count(self):
        for record in self:
            record.appointment_count = self.env['calendar.event'].search_count([
                ('partner_id', '=', record.partner_id.id)
            ])