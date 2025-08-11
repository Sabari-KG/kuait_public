# Copyright 2024 MaiCall
# @author: Ihor Pysmennyi (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
from odoo import models, fields


class EvoAISettings(models.Model):
    _name = 'evo.ai.settings'
    _description = 'AI settings'

    name = fields.Char(required=True)
    auth_token = fields.Char(string="Auth Token/API key", required=True)
    cost = fields.Float(string="Cost/1min.", default=0)
    active = fields.Boolean(default=True)
    service_type = fields.Selection(
        required=True,
        default='unknown',
        selection=[('unknown', 'Unknown')])
