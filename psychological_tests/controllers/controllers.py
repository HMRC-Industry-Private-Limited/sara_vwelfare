from odoo import http
from odoo.http import request, Controller, route
from odoo import fields
from datetime import datetime


class PsychologicalTestController(http.Controller):
    # page psychological_tests

    @http.route('/psychological_tests', type='http', auth='public', website=True, csrf=True)
    def psychological_tests(self, **kwargs):
        user = request.env.user
        # المستخدم الداخلي (له صلاحيات كاملة)
        if user.has_group('base.group_user'):
            pass  # لا نمنعه من شيء

        # المستخدم الزائر
        elif user._is_public():
            show_for_public = request.env['ir.config_parameter'].sudo().get_param('psychological_tests.show_for_public')
            if show_for_public != 'True':
                return request.redirect('')

        # مستخدم الموقع (مسجل في البوابة)
        else:
            show_for_loggedin = request.env['ir.config_parameter'].sudo().get_param('psychological_tests.show_for_loggedin')
            if show_for_loggedin != 'True':
                return request.redirect('/')

        psychological_tests = request.env['psychological.test'].sudo().search([('website_published', '=', True)])
        tests_types = request.env['test.type'].sudo().search([])

        return request.render(
                'psychological_tests.test_list_template', {
                        'psychological_tests': psychological_tests,
                        'tests_types'        : tests_types,
                })

    # page detail template
    @http.route('/test_type/<model("test.type"):test>', type='http', auth='public', website=True, csrf=True)
    def test_detail(self, test, **kwargs):
        user = request.env.user

        # Internal user (موظف داخلي في Odoo)
        if user.has_group('base.group_user'):
            pass  # السماح دائماً

        # زائر (Public user)
        # Guest user
        elif user._is_public():
            show_for_public = request.env['ir.config_parameter'].sudo().get_param('psychological_tests.show_for_public')
            if show_for_public != 'True':
                return request.redirect('/')

        # مستخدم مسجل في الموقع
        # Logged-in website user
        else:
            show_for_loggedin = request.env['ir.config_parameter'].sudo().get_param('psychological_tests.show_for_loggedin')
            if show_for_loggedin != 'True':
                return request.redirect('/')

        return request.render('psychological_tests.test_detail_template', {'test': test})

    ##########
    # page start test questions
    @http.route('/start_test/<model("test.type"):test>', type='http', auth='public', website=True, csrf=True)
    def start_test(self, test, **kwargs):
        user = request.env.user

        # جلب الإعدادات
        show_for_public = request.env['ir.config_parameter'].sudo().get_param('psychological_tests.show_for_public') == 'True'
        show_for_loggedin = request.env['ir.config_parameter'].sudo().get_param('psychological_tests.show_for_loggedin') == 'True'

        # التحقق من نوع المستخدم
        if user.has_group('base.group_user'):
            # مستخدم داخلي: يدخل عادي
            pass

        elif user._is_public():
            # زائر: حسب صلاحية show_for_public
            if not show_for_public:
                return request.redirect('/')  # أو صفحة خطأ حسب رغبتك

        else:
            # مستخدم مسجل: حسب صلاحية show_for_loggedin
            if not show_for_loggedin:
                return request.redirect('/')  # أو صفحة خطأ حسب رغبتك

        # لو اجتاز التحقق بنجاح، نعرض الاختبار

        questions = test.question_ids
        if not questions:
            return request.render(
                    'psychological_tests.start_test_template', {
                            'test' : test,
                            'error': 'لا توجد أسئلة متاحة لهذا الاختبار حاليًا. يرجى المحاولة لاحقًا.'
                    })

        if 'current_question_index' not in request.session:
            request.session['current_question_index'] = 0

        total_questions = len(questions)
        current_index = request.session['current_question_index']
        progress = float((current_index + 1) / total_questions * 100) if total_questions else 0.0
        progress_formatted = f"{progress:.0f}%"

        return request.render(
                'psychological_tests.start_test_template', {
                        'test'              : test,
                        'questions'         : questions,
                        'total_questions'   : total_questions,
                        'current_index'     : current_index,
                        'progress'          : progress,
                        'progress_formatted': progress_formatted,
                })

    # لإنشاء سجل واحد في test.type.answer يحتوي على جميع إجابات الأسئلة في answer_line_ids.
    @http.route('/submit_test/<model("test.type"):test>', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def submit_test(self, test, **kwargs):
        user = request.env.user

        # جلب الإعدادات
        show_for_public = request.env['ir.config_parameter'].sudo().get_param('psychological_tests.show_for_public') == 'True'
        show_for_loggedin = request.env['ir.config_parameter'].sudo().get_param('psychological_tests.show_for_loggedin') == 'True'

        # التحقق من نوع المستخدم وصلاحية العرض
        if user.has_group('base.group_user'):
            # مستخدم داخلي: يدخل عادي
            pass
        elif user._is_public():
            # زائر: حسب صلاحية show_for_public
            if not show_for_public:
                return request.redirect('/')
        else:
            # مستخدم مسجل: حسب صلاحية show_for_loggedin
            if not show_for_loggedin:
                return request.redirect('/')

        # تابع معالجة إرسال الاختبار بعد التحقق
        submission_date = fields.Datetime.now()
        max_score = sum(question.score for question in test.question_ids)

        # إنشاء سجل إجابة رئيسي
        answer_vals = {
                'user_id'        : user.id,
                'test_id'        : test.id,
                'submission_date': submission_date,
                'answer_line_ids': [],
        }

        # جمع إجابات الأسئلة
        for question in test.question_ids:
            line_vals = {
                    'question_id': question.id,
            }

            if question.question_type in ['multiple_choice', 'checkbox']:
                selected_option_ids = []
                form_key = f'question_{question.id}'
                if question.question_type == 'multiple_choice':
                    option_id = kwargs.get(form_key)
                    if option_id:
                        selected_option_ids.append(int(option_id))
                else:  # checkbox
                    form_key_array = f'{form_key}[]'
                    option_ids = request.httprequest.form.getlist(form_key_array)
                    if not option_ids:
                        option_ids = kwargs.get(form_key_array, [])
                        if isinstance(option_ids, str):
                            option_ids = [option_ids]
                    selected_option_ids = [int(opt) for opt in option_ids if opt]
                line_vals['selected_option_ids'] = [(6, 0, selected_option_ids)]
                line_vals['text_answer'] = False
            else:  # text
                text_answer = kwargs.get(f'question_{question.id}', '').strip()
                text_answer = ' '.join(text_answer.split())
                line_vals['text_answer'] = text_answer
                line_vals['selected_option_ids'] = [(5, 0, 0)]

            answer_vals['answer_line_ids'].append((0, 0, line_vals))

        # إنشاء سجل الإجابة
        answer = request.env['test.type.answer'].sudo().create(answer_vals)
        total_score = answer.total_score

        # استرجاع النتيجة
        result_line = test.get_result_line_by_score(total_score)
        result_text = result_line.result_text if result_line else 'لم يتم تحديد النتيجة.'
        result_class = result_line.result_class if result_line else 'secondary'

        # إعادة ضبط الجلسة
        request.session['current_question_index'] = 0

        # إنشاء رابط Odoo لعرض الإجابة
        odoo_link = f"/web#id={answer.id}&model=test.type.answer&view_type=form"

        # عرض النتيجة
        return request.render(
                'psychological_tests.test_result_template', {
                        'test'        : test,
                        'total_score' : total_score,
                        'max_score'   : max_score,
                        'result_text' : result_text,
                        'result_class': result_class,
                        'odoo_link'   : odoo_link,
                })
################################################################################
# دا بيعمل لكل سوال واجابة حقل جديد لكل مستخدم
# page submit test questions
# @http.route('/submit_test/<model("test.type"):test>', type='http', auth='public', website=True, methods=['POST'], csrf=True)
# def submit_test(self, test, **kwargs):
#     total_score = 0
#     max_score = 0
#     submission_date = fields.Datetime.now()
#
#     # جمع النقاط من الأسئلة
#     for question in test.question_ids:
#         max_score += question.score  # جمع درجات الأسئلة
#
#         answer_vals = {
#                 'user_id'        : request.env.user.id,
#                 'test_id'        : test.id,
#                 'submission_date': submission_date,  # استخدام نفس قيمة التاريخ لكل الإجابات
#                 'question_id'    : question.id,
#         }
#
#         if question.question_type in ['multiple_choice', 'checkbox']:
#             selected_option_ids = []
#             form_key = f'question_{question.id}'
#             if question.question_type == 'multiple_choice':
#                 option_id = kwargs.get(form_key)
#                 if option_id:
#                     selected_option_ids.append(int(option_id))
#             else:  # checkbox
#                 form_key_array = f'{form_key}[]'  # Handle checkbox array
#                 option_ids = kwargs.get(form_key_array, [])
#                 if isinstance(option_ids, str):
#                     option_ids = [option_ids]
#                 selected_option_ids = [int(opt) for opt in option_ids if opt]
#             answer_vals['selected_option_ids'] = [(6, 0, selected_option_ids)]
#             answer_vals['text_answer'] = False
#         else:  # text
#             # تنظيف النص المدخل بإزالة المسافات الزائدة
#             text_answer = kwargs.get(f'question_{question.id}', '').strip()
#             # إزالة المسافات الزائدة بين الكلمات إذا لزم الأمر
#             text_answer = ' '.join(text_answer.split())
#             answer_vals['text_answer'] = text_answer
#             answer_vals['selected_option_ids'] = [(5, 0, 0)]
#         # تسجيل الإجابة
#         answer = request.env['test.type.answer'].sudo().create(answer_vals)
#         total_score += answer.score
#
#     # استرجاع النتيجة بناءً على النقاط المحققة
#     result_line = test.get_result_line_by_score(total_score)
#     result_text = result_line.result_text if result_line else 'لم يتم تحديد النتيجة.'
#     result_class = result_line.result_class if result_line else 'secondary'
#
#     # Reset session
#     request.session['current_question_index'] = 0
#
#     # إضافة رابط لعرض الإجابات في واجهة Odoo
#     odoo_link = f"/web#action=psychological_tests.action_test_type_answer&view_type=list&domain=[('user_id', '=', {request.env.user.id}), ('test_id', '=', {test.id}), ('submission_date', '=', '{fields.Datetime.to_string(submission_date)}')]"
#
#     # عرض النتيجة
#     return request.render(
#             'psychological_tests.test_result_template', {
#                     'test'        : test,
#                     'total_score' : total_score,
#                     'max_score'   : max_score,
#                     'result_text' : result_text,
#                     'result_class': result_class,
#                     'odoo_link'   : odoo_link,
#             })
