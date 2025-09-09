from odoo import tools

from odoo import models, fields, api
import base64
import io
from datetime import datetime
import xlsxwriter


class TestTypeStatistics(models.Model):
    _name = 'test.type.statistics'
    _description = 'Test Type Statistics'
    _auto = False
    _rec_name = 'test_id'

    test_id = fields.Many2one('test.type', string='Test', readonly=True)
    result_text = fields.Char(string='Result Category', readonly=True)
    count = fields.Integer(string='Count', readonly=True)
    percentage = fields.Float(string='Percentage (%)', readonly=True)
    total_count = fields.Integer(string='Total Tests', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
                """
                CREATE or REPLACE VIEW %s AS (
                    WITH test_counts AS (
                        SELECT 
                            test_id, 
                            COUNT(*) as total_count 
                        FROM 
                            test_type_answer 
                        GROUP BY 
                            test_id
                    ),
                    result_counts AS (
                        SELECT 
                            a.test_id, 
                            a.result_text, 
                            COUNT(*) as result_count 
                        FROM 
                            test_type_answer a 
                        WHERE 
                            a.result_text IS NOT NULL 
                        GROUP BY 
                            a.test_id, a.result_text
                    )
                    SELECT
                        row_number() OVER () AS id,
                        r.test_id,
                        r.result_text,
                        r.result_count AS count,
                        (r.result_count::float / t.total_count) * 100 AS percentage,
                        t.total_count
                    FROM
                        result_counts r
                    JOIN
                        test_counts t ON r.test_id = t.test_id
                )
            """ % (self._table))
