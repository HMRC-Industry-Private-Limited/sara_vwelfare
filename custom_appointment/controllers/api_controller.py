from odoo import http
from odoo.http import request, Response
import json
from datetime import datetime, timedelta
import ast

class AppointmentAPI(http.Controller):
    
    @http.route('/api/v1/doctors', type='http', auth='public', methods=['GET'], csrf=False)
    def get_doctors(self):
        try:
            # الحصول على قائمة الأطباء المسموح بهم من الإعدادات
            param = request.env['ir.config_parameter'].sudo().get_param('custom_appointment.calendar_doctors', '[]')
            allowed_user_ids = ast.literal_eval(param)
            
            # البحث عن المستخدمين المسموح بهم فقط
            partners = request.env['res.users'].sudo().search([
                ('id', 'in', allowed_user_ids),
                ('doctor_id', '!=', False)
            ])
            
            result = [{
                'id': partner.doctor_id,
                'name': partner.name
            } for partner in partners]
            
            return self._json_response(data={
                'doctors': result,
                'total_count': len(result)
            })
            
        except Exception as e:
            return self._json_response(
                error=str(e),
                status=500
            )
            

    @http.route('/api/v1/appointments/get', type='http', auth='public', methods=['GET'], csrf=False)
    def get_appointments(self, **kwargs):
        try:
            # الحصول على قائمة الأطباء المسموح بهم
            param = request.env['ir.config_parameter'].sudo().get_param('custom_appointment.calendar_doctors', '[]')
            allowed_user_ids = ast.literal_eval(param)
            
            domain = [('user_id', 'in', allowed_user_ids)]
            
            # إضافة فلتر الطبيب إذا تم تحديده
            if kwargs.get('doctor_id'):
                try:
                    doctor_id = int(kwargs['doctor_id'])
                    user = request.env['res.users'].sudo().search([
                        ('doctor_id', '=', doctor_id),
                        ('id', 'in', allowed_user_ids)
                    ], limit=1)
                    if user:
                        domain = [('user_id', '=', user.id)]
                    else:
                        return self._json_response(
                            error='لم يتم العثور على طبيب بهذا المعرف أو غير مصرح له',
                            status=400
                        )
                except ValueError:
                    return self._json_response(
                        error='معرف الطبيب يجب أن يكون رقماً',
                        status=400
                    )
            
            # إضافة فلتر للمواعيد من API فقط
            domain.append(('is_api_appointment', '=', True))
            
            appointments = request.env['calendar.event'].sudo().search(domain)

            result = []
            for appointment in appointments:
                doctor = request.env['res.users'].sudo().browse(appointment.user_id.id)
                result.append({
                    'start_time': appointment.start.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': appointment.stop.strftime('%Y-%m-%d %H:%M:%S'),
                    'doctor_id': doctor.doctor_id if doctor else False
                })
            
            return self._json_response(data={
                'appointments': result,
                'total_count': len(result)
            })
            
        except Exception as e:
            return self._json_response(error=str(e), status=500)


    @http.route('/api/v1/appointments/store', type='http', auth='public', methods=['GET'], csrf=False)
    def create_appointment(self, name, phone, doctor_id, start_time, duration):
        try:
            # الحصول على قائمة الأطباء المسموح بهم
            param = request.env['ir.config_parameter'].sudo().get_param('custom_appointment.calendar_doctors', '[]')
            allowed_user_ids = ast.literal_eval(param)
            
            # التحقق من صحة المعرف doctor_id
            try:
                doctor_id = int(doctor_id)
                user = request.env['res.users'].sudo().search([
                    ('doctor_id', '=', doctor_id),
                    ('id', 'in', allowed_user_ids)
                ], limit=1)
                if not user:
                    return self._json_response(
                        error='معرف الطبيب غير صحيح أو غير مصرح له',
                        status=400
                    )
            except ValueError:
                return self._json_response(
                    error='معرف الطبيب يجب أن يكون رقماً',
                    status=400
                )

            # التحقق من صحة المدة
            try:
                duration = int(duration)
                if duration not in [15, 30, 60]:
                    return self._json_response(
                        error='المدة يجب أن تكون 15 أو 30 أو 60 دقيقة',
                        status=400
                    )
            except ValueError:
                return self._json_response(
                    error='المدة يجب أن تكون رقماً',
                    status=400
                )

            # التحقق من صحة التاريخ والوقت
            try:
                start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                
                # التحقق من أن التاريخ ليس في الماضي
                if start < datetime.now():
                    return self._json_response(
                        error='لا يمكن حجز موعد في تاريخ سابق',
                        status=400
                    )
                
                duration_hours = float(duration) / 60
                stop = start + timedelta(hours=duration_hours)
            except ValueError:
                return self._json_response(
                    error='صيغة التاريخ والوقت غير صحيحة. الصيغة المطلوبة: YYYY-MM-DD HH:MM:SS',
                    status=400
                )

            # التحقق من عدم وجود مواعيد متداخلة
            conflicting_appointments = request.env['calendar.event'].sudo().search([
                ('user_id', '=', user.id),
                '|',
                '&', ('start', '>=', start), ('start', '<', stop),  # يبدأ خلال الموعد الجديد
                '&', ('stop', '>', start), ('stop', '<=', stop),    # ينتهي خلال الموعد الجديد
            ])

            if conflicting_appointments:
                return self._json_response(
                    error='يوجد موعد آخر في نفس الوقت. الرجاء اختيار وقت آخر.',
                    status=400
                )

            # إنشاء الموعد
            vals = {
                'name': name,
                'description': f"Phone: {phone}",
                'user_id': user.id,
                'start': start,
                'stop': stop,
                'duration': duration_hours,
                'is_api_appointment': True,  # إضافة العلامة للمواعيد من API
            }

            appointment = request.env['calendar.event'].sudo().create(vals)

            return self._json_response(data={
                'success': True,
                'appointment': {
                    'start_time': appointment.start.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': appointment.stop.strftime('%Y-%m-%d %H:%M:%S'),
                    'doctor_id': doctor_id
                }
            })

        except Exception as e:
            return self._json_response(
                error=str(e),
                status=500
            )

    def _json_response(self, data=None, error=None, status=200):
        response = {
            'jsonrpc': '2.0',
            'id': None,
        }
        
        if error:
            response['error'] = error
        if data:
            response['result'] = data
            
        return Response(
            json.dumps(response),
            content_type='application/json;charset=utf-8',
            status=status
        ) 