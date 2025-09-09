from odoo import api, fields, models
import requests
from datetime import datetime, timedelta

class AppointmentManager(models.Model):
    _inherit = 'res.users'

    last_sync_time = fields.Datetime(string='Last Sync Time')

    def sync_appointments(self):
        url = "https://klinicat.vwelfare.com/api/v1/appointments/get"
        try:
            params = {}
            if self.last_sync_time:
                params['after'] = self.last_sync_time.strftime('%Y-%m-%d %H:%M:%S')

            response = requests.get(url, params=params)
            response.raise_for_status()
            appointments_data = response.json()

            new_count = 0
            existing_count = 0

            for appointment in appointments_data:
                start_time = datetime.strptime(appointment['start_time'], '%Y-%m-%d %H:%M:%S') - timedelta(hours=3)
                end_time = datetime.strptime(appointment['end_time'], '%Y-%m-%d %H:%M:%S') - timedelta(hours=3)


                doctor = self.env['res.users'].search([('doctor_id', '=', str(appointment['doctor_id']))], limit=1)

                existing_appointment = self.env['calendar.event'].search([
                    ('user_id', '=', doctor.id),
                    ('start', '=', start_time),
                    ('stop', '=', end_time)
                ])
                if not existing_appointment:
                    duration_minutes = int((end_time - start_time).total_seconds() / 60)

                    appointment_type = self.env['appointment.type'].search([
                        ('duration_minutes', '=', duration_minutes),
                        ('doctor_ids', 'in', [doctor.id])
                    ], limit=1)
                    # إنشاء أو البحث عن شريك للمريض
                    partner = self.env['res.partner'].search([
                        ('email', '=', appointment.get('email')),
                        '|', ('phone', '=', appointment.get('phone')),
                        ('mobile', '=', appointment.get('phone'))
                    ], limit=1)
                    if not partner and appointment.get('name'):
                        partner = self.env['res.partner'].create({
                            'name': appointment.get('name'),
                            'email': appointment.get('email'),
                            'phone': appointment.get('phone'),
                        })
                    # تجهيز قائمة المشاركين في الموعد - Ensure we only include valid partners
                    attendee_ids = []
                    if doctor and doctor.partner_id and doctor.partner_id.id:
                        attendee_ids.append(doctor.partner_id.id)
                    if partner and partner.id:
                        attendee_ids.append(partner.id)

                    # Make sure we have at least one valid partner
                    if not attendee_ids:
                        continue

                    partner_ids = [(6, 0, attendee_ids)]

                    # تأكد من وجود إعدادات البريد الإلكتروني
                    mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
                    no_mail_event = not mail_server

                    # Create and store the calendar event
                    self.env['calendar.event'].with_context(
                        mail_create_nolog=no_mail_event,  # تعطيل سجلات البريد
                        mail_create_nosubscribe=True,     # تعطيل الاشتراك التلقائي
                        mail_notrack=no_mail_event        # تعطيل تتبع البريد
                    ).create({
                        'name': appointment.get('name', f'Appointment for Dr. {doctor.name}'),
                        'start': start_time,
                        'stop': end_time,
                        'user_id': doctor.id,
                        'is_imported': True,
                        'appointment_type_id': appointment_type.id if appointment_type else False,
                        'partner_ids': partner_ids,
                    })
                    new_count += 1
                else:
                    existing_count += 1

            self.write({'last_sync_time': fields.Datetime.now()})

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Added {new_count} new appointments, skipped {existing_count} existing appointments',
                    'type': 'success',
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
