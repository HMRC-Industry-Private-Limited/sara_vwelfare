from odoo import fields, models, api
import ast

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    calendar_doctors = fields.Many2many(
        'res.users',
        'calendar_doctors_users_rel',
        'config_id',
        'user_id',
        string='الأطباء المتاحين',
        domain=[('doctor_id', '!=', False)],
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'custom_appointment.calendar_doctors',
            str(self.calendar_doctors.ids)
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo().get_param('custom_appointment.calendar_doctors', '[]')
        try:
            doctor_ids = ast.literal_eval(param)
            res.update(calendar_doctors=[(6, 0, doctor_ids)])
        except:
            res.update(calendar_doctors=[(6, 0, [])])
        return res 