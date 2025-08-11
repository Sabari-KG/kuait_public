# Copyright 2025 MaiCall
# @author: Serhii Mishchenko (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
from odoo import models, fields


class EvoCallCustomRelated(models.Model):
    _name = 'evo.call.custom.related'
    _description = 'EVO Call Custom Related'
    _order = "sequence, id desc"

    name = fields.Char(required=True)
    evo_call_custom_id = fields.Many2one('evo.call.custom', required=True, ondelete='cascade')
    model = fields.Char(related="evo_call_custom_id.model_id.model")
    field_id = fields.Many2one(
        'ir.model.fields',
        ondelete='cascade',
        domain="[('model', '=', model)]"
    )
    field_char = fields.Char("Field")
    sequence = fields.Integer(default=1)
