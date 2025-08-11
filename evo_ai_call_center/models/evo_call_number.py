# Copyright 2025 MaiCall
# @author: Ihor Pysmennyi (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).

from odoo import fields, models


class EvoCallNumber(models.Model):
    _name = 'evo.call.number'
    _description = 'EVO Call Number'

    name = fields.Char(required=True)
    service_id = fields.Many2one(
        'evo.call.service.settings', required=True, index=True)
    is_busy = fields.Boolean(default=False)
    active = fields.Boolean(default=True)
