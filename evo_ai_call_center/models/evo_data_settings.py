# Copyright 2025 MaiCall
# @author: Serhii Mishchenko (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).

from odoo import models, fields


class EvoCallServiceSettings(models.Model):
    _name = 'evo.data.settings'
    _description = 'Data Settings'

    name = fields.Char(required=True)
    prompt = fields.Text(string='AI Prompt')
    active = fields.Boolean(default=True)
