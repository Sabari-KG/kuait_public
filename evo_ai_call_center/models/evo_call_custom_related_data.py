# Copyright 2025 MaiCall
# @author: Serhii Mishchenko (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
from odoo import models, fields


class EvoCallCustomRelatedData(models.Model):
    _name = 'evo.call.custom.related.data'

    call_id = fields.Many2one('evo.call')
    # model_id = fields.Many2one('ir.model')
    # model_name = fields.Char(related='model_id.model')
    model_name = fields.Char()
    rec_id = fields.Integer()

    def get_record(self) -> models.Model:
        """ Get record """
        self.ensure_one()
        return self.env[self.model_name].browse(self.rec_id)
