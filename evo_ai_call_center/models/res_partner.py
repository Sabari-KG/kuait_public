# Copyright 2025 MaiCall
# @author: Ihor Pysmennyi (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    campaign_ids = fields.Many2many('evo.call.campaign', string="Campaigns")
    last_call_date = fields.Date(string="Last Call", readonly=True)

    def action_get_calls(self):
        """ Button action for button box. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Calls',
            'view_mode': 'tree,form,pivot,graph',
            'res_model': 'evo.call',
            'domain': [('partner_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_get_campaigns(self):
        """ Button action for button box. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Campaigns',
            'view_mode': 'tree,form',
            'res_model': 'evo.call.campaign',
            'domain': [('partner_ids', '=', self.id)],
            'context': "{'create': False}"
        }
