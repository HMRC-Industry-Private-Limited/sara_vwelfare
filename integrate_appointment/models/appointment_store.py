from odoo import models, fields, api
import requests
from datetime import datetime
from datetime import timedelta


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    is_imported = fields.Boolean(string="Imported from API", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        print("🚀 create() method in CalendarEvent is being executed!")
        events = super().create(vals_list)

        for event in events:
            if event.is_imported:
                continue  # تخطي إرسال المواعيد المستوردة

            try:
                api_url = "https://klinicat.vwelfare.com/api/v1/appointments/store"

                start_time = (event.start + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
                duration = int((event.stop - event.start).total_seconds() / 60)

                doctor_id = event.user_id.doctor_id if event.user_id.doctor_id else 'UNKNOWN'
                patient_name = event.patient_name if event.patient_name else 'Unknown'
                phone_number = event.partner_ids and (event.partner_ids[1].phone or event.partner_ids[1].mobile) or 'Unknown'

                params = {
                    'name': patient_name,
                    'phone': phone_number,
                    'doctor_id': doctor_id,
                    'start_time': start_time,
                    'duration': duration
                }

                print("====== Sending Data to API ======")
                print("API URL:", api_url)
                print("Payload:", params)

                response = requests.post(api_url, json=params)
                print("Response Status Code:", response.status_code)
                print("Response Content:", response.text)

                response.raise_for_status()

                event.message_post(body=f"✅ تم إرسال الموعد بنجاح إلى النظام الخارجي: {response.json()}")

            except Exception as e:
                print(f"⚠️ خطأ أثناء إرسال البيانات: {str(e)}")
                event.message_post(body=f"⚠️ فشل في إرسال البيانات إلى النظام الخارجي: {str(e)}")

        return events
