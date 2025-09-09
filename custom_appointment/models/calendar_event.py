from odoo import models, fields, api
import ast
import requests
import json

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    is_api_appointment = fields.Boolean(string="API Appointment", default=False)

    @api.model
    def create(self, vals):
        # إنشاء الموعد في Odoo
        appointment = super(CalendarEvent, self).create(vals)
        
        # إذا كان الموعد مش من API، نبعته للـ API
        if not vals.get('is_api_appointment'):
            try:
                # احصل على API URL من system parameters
                api_url = self.env['ir.config_parameter'].sudo().get_param('appointment_api_url')
                
                if api_url:
                    data = {
                        'name': appointment.name,
                        'phone': appointment.description,  # افترضنا إن الphone في الdescription
                        'doctor_id': appointment.user_id.doctor_id,
                        'start_time': appointment.start.strftime('%Y-%m-%d %H:%M:%S'),
                        'duration': int(appointment.duration * 60)  # تحويل الساعات لدقائق
                    }
                    
                    # إرسال الموعد للـ API
                    response = requests.get(f"{api_url}/api/v1/appointments/store", params=data)
                    
                    if response.status_code != 200:
                        # يمكنك إضافة log هنا لتتبع الأخطاء
                        pass
                        
            except Exception as e:
                # يمكنك إضافة log هنا لتتبع الأخطاء
                pass
                
        return appointment


