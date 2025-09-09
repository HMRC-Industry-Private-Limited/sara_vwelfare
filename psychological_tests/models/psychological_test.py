# © 2025 [Mahmoud Abd Al-Razek Hussein]. All rights reserved.
# Unauthorized use, distribution or modification of this file is strictly prohibited.

from odoo import models, fields


class PersonalityQuestion(models.Model):
    _name = 'psychological.test'
    _description = 'Psychological Test Question'

    name = fields.Char(string="Test Name", required=True)
    description = fields.Text(string="Description")
    image = fields.Binary(string="Test Image")
    website_published = fields.Boolean(string="Published on Website", default=True)
