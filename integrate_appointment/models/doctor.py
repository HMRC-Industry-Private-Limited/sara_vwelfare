from odoo import api, fields, models
import requests

class ResUsers(models.Model):
    _inherit = 'res.users'

    doctor_id = fields.Char(string='Doctor ID')
    
    @api.model
    def create_portal_doctor(self, doctor_id, name):
        portal_group = self.env.ref('base.group_portal')
        
        vals = {
            'name': name,
            'login': f'doctor_{doctor_id}@klinicat.com',
            'password': 'default_password',
            'doctor_id': doctor_id,
            'groups_id': [(6, 0, [portal_group.id])],
            'sel_groups_1_9_10': 9,  # Portal User
        }
        
        user = self.create(vals)
        return user

    def fetch_and_create_doctors(self):
        url = "https://klinicat.vwelfare.com/api/v1/doctors"
        try:
            response = requests.get(url)
            doctors = response.json()
            
            new_doctors = 0
            existing_doctors = 0
            
            for doctor in doctors:
                existing_user = self.search([('doctor_id', '=', str(doctor['id']))])
                if not existing_user:
                    self.create_portal_doctor(str(doctor['id']), doctor['name'])
                    new_doctors += 1
                else:
                    existing_doctors += 1
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import Result',
                    'message': f'New doctors created: {new_doctors}\nExisting doctors skipped: {existing_doctors}',
                    'type': 'info',
                    'sticky': False,
                }
            }
                
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
