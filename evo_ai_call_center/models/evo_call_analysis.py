# Copyright 2024 MaiCall
# @author: Ihor Pysmennyi (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
from odoo import models, fields


class EvoCallAnalysis(models.Model):
    _name = 'evo.call.analysis'
    _description = 'EVO Calls Analysis'
    _order = "id desc"

    name = fields.Char(required=True)
    rationale = fields.Text()
    value = fields.Char()
    call_id = fields.Many2one('evo.call', required=True, ondelete='cascade')
    campaign_id = fields.Many2one(
        'evo.call.campaign',
        related="call_id.campaign_id",
        store=True,
    )
    analysis_type = fields.Selection(
        selection=[
            ('data_collection_results', 'Data collection Results'),
            ('evaluation_criteria_results', 'Evaluation Criteria Results')],
        default='data_collection_results',
        readonly=True,
        required=True)
