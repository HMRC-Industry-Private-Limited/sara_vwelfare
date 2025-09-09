# © 2025 [Mahmoud Abd Al-Razek Hussein]. All rights reserved.
# Unauthorized use, distribution or modification of this file is strictly prohibited.

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from fuzzywuzzy import fuzz


# الاختبار
class TestType(models.Model):
    _name = 'test.type'
    _description = 'Test Type'

    name = fields.Char(string='Test Name', required=True)
    description = fields.Text(string='Description')
    image = fields.Binary(string='Image')
    question_ids = fields.One2many('test.type.question', 'test_id', string='Questions')  # ربط الأسئلة بالاختبار
    result_line_ids = fields.One2many('test.type.result.line', 'test_id', string='Result Lines')

    total_score = fields.Integer(string="Total Score", compute="_compute_total_score", store=True)

    @api.depends('question_ids.score')
    def _compute_total_score(self):
        for record in self:
            record.total_score = sum(record.question_ids.mapped('score'))

    def get_result_line_by_score(self, score):
        # العثور على النتيجة المناسبة بناءً على النقاط
        result_line = self.env['test.type.result.line'].search(
                [
                        ('test_id', '=', self.id),
                        ('min_score', '<=', score),
                        ('max_score', '>=', score)
                ], limit=1)
        return result_line


# الأسئلة
class TestTypeQuestion(models.Model):
    _name = 'test.type.question'
    _description = 'Test Type Question'

    name = fields.Char(string='Question Text', required=True)
    test_id = fields.Many2one('test.type', string='Test', required=True, ondelete='cascade')
    question_type = fields.Selection(
            [
                    ('multiple_choice', 'Multiple Choice'),
                    ('checkbox', 'Checkbox'),
                    ('text', 'Text'),
            ], string='Question Type', required=True, default='multiple_choice')
    option_ids = fields.One2many('test.type.option', 'question_id', string='Options')
    score = fields.Integer(string='Total Score for Options', default=0)

    # @api.constrains('option_ids', 'question_type')
    # def _check_options_required(self):
    #     for question in self:
    #         if question.question_type in ['multiple_choice', 'checkbox'] and not question.option_ids:
    #             raise ValidationError("يجب إدخال خيارات للأسئلة من نوع 'اختيار متعدد' أو 'خانة اختيار'!")
    #         if question.question_type == 'multiple_choice' and len(question.option_ids) < 2:
    #             raise ValidationError("يجب إدخال خيارين على الأقل لسؤال من نوع 'اختيار متعدد'!")

    @api.constrains('option_ids', 'score')
    def _check_option_scores(self):
        for question in self:
            if question.score > 0:
                total_option_score = sum(option.score for option in question.option_ids)
                if total_option_score > question.score:
                    raise ValidationError(
                            f"مجموع درجات خيارات السؤال '{question.name} ({total_option_score})' "
                            f" ) لا يمكن أن يتجاوز درجة السؤال {question.score})!"
                    )


# الخيارات
class TestTypeOption(models.Model):
    _name = 'test.type.option'
    _description = 'Test Type Option'
    _rec_name = 'option_text'

    question_id = fields.Many2one('test.type.question', string='Question', required=True, ondelete='cascade')
    option_text = fields.Char(string='Option Text', required=True)
    score = fields.Integer(string='Score', default=0)  # درجة الخيار


# النتايج
class TestTypeResultLine(models.Model):
    _name = 'test.type.result.line'
    _description = 'Test Result Line'

    test_id = fields.Many2one('test.type', string='Test', required=True, ondelete='cascade')
    min_score = fields.Integer(string='Minimum Score', required=True)
    max_score = fields.Integer(string='Maximum Score', required=True)
    result_text = fields.Text(string='Result Text', required=True)
    result_class = fields.Selection(
            [
                    ('success', 'Success'),
                    ('warning', 'Warning'),
                    ('danger', 'Danger')
            ], string='CSS Class', default='success')

    @api.constrains('min_score', 'max_score')
    def _check_score_range(self):
        for rec in self:
            if rec.min_score > rec.max_score:
                raise ValidationError("الحد الأدنى لا يمكن أن يكون أكبر من الحد الأقصى!")

    @api.constrains('min_score', 'max_score')
    def _check_max_score(self):
        for rec in self:
            if rec.max_score > rec.test_id.total_score:
                raise ValidationError(
                        f"الحد الأقصى للنقاط ({rec.max_score}) لا يمكن أن يكون أكبر من مجموع نقاط الاختبار "
                        f"({rec.test_id.name}) والذي مقداره ({rec.test_id.total_score})."
                )


# الاجابات
class TestTypeAnswer(models.Model):
    _name = 'test.type.answer'
    _description = 'Test Type Answer'
    _rec_name = 'display_name'
    _order = 'submission_date desc'

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    test_id = fields.Many2one('test.type', string='Test', required=True)
    submission_date = fields.Datetime(string='Submission Date', default=fields.Datetime.now)
    answer_line_ids = fields.One2many('test.type.answer.line', 'answer_id', string='Answer Lines')
    total_score = fields.Integer(string='Total Score', compute='_compute_total_score', store=True)
    max_score = fields.Integer(string='Maximum Score', compute='_compute_max_score', store=True)
    result_text = fields.Text(string='Result Text', compute='_compute_result_text', store=True)

    # percentage_in_group = fields.Float(
    #         string='النسبة (%)',
    #         compute='_compute_percentage_in_group',
    #         store=True,
    #         readonly=True,
    # )
    #
    # @api.depends('test_id', 'result_text', 'answer_line_ids', 'total_score')
    # def _compute_percentage_in_group(self):
    #     all_records = self.env['test.type.answer'].search([])
    #     test_totals = {}
    #     for rec in all_records:
    #         test_id = rec.test_id.id
    #         if test_id:
    #             test_totals[test_id] = test_totals.get(test_id, 0) + 1
    #
    #     for record in self:
    #         test_id = record.test_id.id
    #         result_text = record.result_text
    #
    #         total_for_test = test_totals.get(test_id, 0)
    #         if test_id and result_text and total_for_test > 0:
    #             same_result_count = sum(
    #                     1 for rec in all_records
    #                     if rec.test_id.id == test_id and rec.result_text == result_text
    #             )
    #             percentage = round((same_result_count / total_for_test) * 100, 2)
    #
    #             # ✅ Debug:
    #             print(f"Test ID: {test_id}, Result: {result_text}, Same: {same_result_count}, Total: {total_for_test}, Percentage: {percentage}")
    #
    #             record.percentage_in_group = percentage
    #         else:
    #             record.percentage_in_group = 0

    def _compute_display_name(self):
        for answer in self:
            if answer.test_id:
                answer.display_name = f"{answer.test_id.name} - {answer.submission_date}"
            else:
                answer.display_name = "New Answer"

    @api.depends('answer_line_ids.score')
    def _compute_total_score(self):
        for answer in self:
            answer.total_score = sum(line.score for line in answer.answer_line_ids)

    @api.depends('test_id')
    def _compute_max_score(self):
        for answer in self:
            answer.max_score = answer.test_id.total_score if answer.test_id else 0

    @api.depends('total_score', 'test_id')
    def _compute_result_text(self):
        for answer in self:
            if answer.test_id and answer.total_score is not None:
                result_line = answer.test_id.get_result_line_by_score(answer.total_score)
                answer.result_text = result_line.result_text if result_line else 'لم يتم تحديد النتيجة.'
            else:
                answer.result_text = 'لم يتم تحديد النتيجة.'

    @api.model
    def get_user_test_result(self, test_id, user_id=None, submission_date=None):
        """الحصول على نتيجة اختبار المستخدم"""
        if not user_id:
            user_id = self.env.user.id

        domain = [('test_id', '=', test_id), ('user_id', '=', user_id)]
        if submission_date:
            day_start = fields.Datetime.from_string(submission_date).replace(hour=0, minute=0, second=0)
            day_end = fields.Datetime.from_string(submission_date).replace(hour=23, minute=59, second=59)
            domain.extend(
                    [
                            ('submission_date', '>=', fields.Datetime.to_string(day_start)),
                            ('submission_date', '<=', fields.Datetime.to_string(day_end))
                    ])

        answer = self.search(domain, limit=1)
        if not answer:
            return False

        test = self.env['test.type'].browse(test_id)
        result_line = test.get_result_line_by_score(answer.total_score)

        return {
                'user_id'        : user_id,
                'test_id'        : test_id,
                'submission_date': answer.submission_date,
                'total_score'    : answer.total_score,
                'max_score'      : test.total_score,
                'result_text'    : result_line.result_text if result_line else 'لم يتم تحديد النتيجة.',
                'result_class'   : result_line.result_class if result_line else 'secondary',
                'answer_lines'   : answer.answer_line_ids,
        }


# اجابات الاختبار لكل مستخدم
class TestTypeAnswerLine(models.Model):
    _name = 'test.type.answer.line'
    _description = 'Test Type Answer Line'

    answer_id = fields.Many2one('test.type.answer', string='Answer', required=True, ondelete='cascade')
    question_id = fields.Many2one('test.type.question', string='Question', required=True)
    selected_option_ids = fields.Many2many('test.type.option', string='Selected Options')
    text_answer = fields.Text(string='Text Answer')
    score = fields.Integer(string='Score', compute='_compute_score', store=True)
    question_type = fields.Selection(related='question_id.question_type', string='Question Type', store=True)
    question_text = fields.Char(related='question_id.name', string='Question Text', store=True)
    max_score = fields.Integer(related='question_id.score', string='Maximum Score', store=True)

    @api.depends('selected_option_ids', 'text_answer', 'question_id', 'question_id.question_type')
    def _compute_score(self):
        for line in self:
            if line.question_id.question_type in ['multiple_choice', 'checkbox']:
                line.score = sum(option.score for option in line.selected_option_ids)
            elif line.question_id.question_type == 'text' and line.text_answer:
                answer_text = line.text_answer.strip().lower()
                best_score = 0
                best_option = None
                for option in line.question_id.option_ids:
                    option_text = option.option_text.strip().lower()
                    similarity = fuzz.partial_ratio(option_text, answer_text)
                    if similarity > 90 and similarity > best_score:
                        best_score = similarity
                        best_option = option
                line.score = best_option.score if best_option else 0
                print(
                        f"Text answer for question {line.question_id.name}: {line.text_answer}, "
                        f"Matched option: {best_option.option_text if best_option else 'None'}, "
                        f"Similarity: {best_score}, Score: {line.score}"
                )
            else:
                line.score = 0

    # @api.depends('selected_option_ids', 'text_answer', 'question_id', 'question_id.question_type')
    # def _compute_score(self):
    #     for line in self:
    #         if line.question_id.question_type in ['multiple_choice', 'checkbox']:
    #             # حساب مجموع درجات كل الخيارات المحددة
    #             line.score = sum(option.score for option in line.selected_option_ids)
    #         elif line.question_id.question_type == 'text' and line.text_answer:
    #             # البحث عن خيار يتطابق مع الإجابة النصية
    #             matching_option = line.question_id.option_ids.filtered(
    #                     lambda opt: opt.option_text.strip().lower() == line.text_answer.strip().lower()
    #             )
    #             line.score = matching_option.score if matching_option else 0
    #         else:
    #             line.score = 0

#############################################
# دا بيعمل لكل سوال واجابة حقل جديد لكل مستخدم
# class TestTypeAnswer(models.Model):
#     _name = 'test.type.answer'
#     _description = 'Test Type Answer'
#     _rec_name = 'display_name'
#     _order = 'submission_date desc, test_id, question_id'
#     user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
#     test_id = fields.Many2one('test.type', string='Test', required=True)
#     question_id = fields.Many2one('test.type.question', string='Question', required=True)
#     submission_date = fields.Datetime(string='Submission Date', default=fields.Datetime.now)
#     selected_option_ids = fields.Many2many('test.type.option', string='Selected Options')  # لتشيك بوكس أو اختيار متعدد
#     text_answer = fields.Text(string='Text Answer')  # للإجابات النصية
#     score = fields.Integer(string='Score', compute='_compute_score', store=True)
#
#     # حقول جديدة لتسهيل العرض
#     display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
#     question_type = fields.Selection(related='question_id.question_type', string='Question Type', store=True)
#     question_text = fields.Char(related='question_id.name', string='Question Text', store=True)
#     max_score = fields.Integer(related='question_id.score', string='Maximum Score', store=True)
#
#     # حقول مجمعة لاستخدامها في العرض
#     submission_group = fields.Char(string='Submission Group', compute='_compute_submission_group', store=True)
#
#     # إضافة حقل لحساب أسماء الخيارات المحددة
#     selected_option_names = fields.Char(string='Selected Option Names', compute='_compute_selected_option_names')
#
#     @api.depends('user_id', 'test_id', 'submission_date')
#     def _compute_submission_group(self):
#         """تجميع الإجابات حسب المستخدم والاختبار وتاريخ التقديم"""
#         for answer in self:
#             if answer.submission_date:
#                 date_str = fields.Datetime.to_string(answer.submission_date)[:10]  # اليوم فقط
#                 answer.submission_group = f"{answer.user_id.id}-{answer.test_id.id}-{date_str}"
#             else:
#                 answer.submission_group = f"{answer.user_id.id}-{answer.test_id.id}"
#
#     @api.depends('question_id', 'test_id')
#     def _compute_display_name(self):
#         for answer in self:
#             if answer.question_id and answer.test_id:
#                 answer.display_name = f"{answer.test_id.name} - {answer.question_id.name}"
#             else:
#                 answer.display_name = "New Answer"
#
#     @api.depends('selected_option_ids', 'question_id')
#     def _compute_score(self):
#         for answer in self:
#             if answer.question_id.question_type in ['multiple_choice', 'checkbox']:
#                 answer.score = sum(option.score for option in answer.selected_option_ids)
#             else:
#                 answer.score = 0  # يمكنك إضافة منطق للإجابات النصية لاحقًا
#
#     @api.model
#     def get_total_score(self, test_id, user_id):
#         """تجميع درجات الإجابات لمستخدم في اختبار معين"""
#         answers = self.search([('test_id', '=', test_id), ('user_id', '=', user_id)])
#         return sum(answer.score for answer in answers)
#
#     @api.model
#     def get_user_test_answers(self, test_id, user_id=None, submission_date=None):
#         """الحصول على جميع إجابات المستخدم لاختبار معين"""
#         if not user_id:
#             user_id = self.env.user.id
#
#         domain = [('test_id', '=', test_id), ('user_id', '=', user_id)]
#
#         # إذا تم تحديد تاريخ التقديم، نضيفه إلى شروط البحث
#         if submission_date:
#             day_start = fields.Datetime.from_string(submission_date).replace(hour=0, minute=0, second=0)
#             day_end = fields.Datetime.from_string(submission_date).replace(hour=23, minute=59, second=59)
#             domain.extend(
#                     [
#                             ('submission_date', '>=', fields.Datetime.to_string(day_start)),
#                             ('submission_date', '<=', fields.Datetime.to_string(day_end))
#                     ])
#
#         return self.search(domain)
#
#     @api.model
#     def get_user_test_result(self, test_id, user_id=None, submission_date=None):
#         """الحصول على نتيجة اختبار المستخدم"""
#         answers = self.get_user_test_answers(test_id, user_id, submission_date)
#
#         if not answers:
#             return False
#
#         total_score = sum(answer.score for answer in answers)
#         test = self.env['test.type'].browse(test_id)
#         max_score = test.total_score
#
#         result_line = test.get_result_line_by_score(total_score)
#
#         return {
#                 'user_id'        : user_id or self.env.user.id,
#                 'test_id'        : test_id,
#                 'submission_date': answers[0].submission_date,
#                 'total_score'    : total_score,
#                 'max_score'      : max_score,
#                 'result_text'    : result_line.result_text if result_line else 'لم يتم تحديد النتيجة.',
#                 'result_class'   : result_line.result_class if result_line else 'secondary',
#                 'answers'        : answers,
#         }
#
