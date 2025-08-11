# Copyright 2024 MaiCall
# @author: Ihor Pysmennyi (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
import random
import re
from typing import List, Dict, Any
import logging
from odoo import models, fields, _, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class EvoCallCampaign(models.Model):
    _name = 'evo.call.campaign'
    _inherit = 'mail.thread'
    _description = 'EVO Call Campaign'
    _order = 'id DESC'

    name = fields.Char(required=True)
    partner_ids = fields.Many2many(
        'res.partner', string="Contacts", required=True, copy=False)
    call_setting_id = fields.Many2one(
        'evo.call.service.settings', string='Call service', required=True)
    call_number_ids = fields.One2many(related='call_setting_id.number_ids')
    number_ids = fields.Many2many(
        comodel_name='evo.call.number',
        string="Numbers",
        required=True
    )
    state = fields.Selection(
        required=True,
        copy=False,
        default='new',
        tracking=True,
        selection=[
            ('new', 'New'),
            ('go', 'In Progress'),
            ('paused', 'Paused'),
            ('stop', 'Stopped')])
    call_ids = fields.One2many(
        'evo.call', 'campaign_id', string='Calls', copy=False)
    custom_ids = fields.One2many(
        'evo.call.custom',
        'campaign_id',
        string='Customizations',
        copy=True)
    # open AI settings
    start_text = fields.Text(
        string='First message',
        required=True,
        help='First message to Assistant to start a dialog.')
    prompt = fields.Text(string='AI Prompt Template', required=True)
    ai_setting_id = fields.Many2one(
        'evo.ai.settings', string='AI setting', required=True)
    service_type = fields.Selection(related="ai_setting_id.service_type")
    language = fields.Many2one('res.lang')

    @api.onchange('call_setting_id')
    def onchange_call_setting_id(self):
        for record in self:
            record.number_ids = record.call_setting_id.number_ids

    # pylint: disable=W8102
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _("%s (copy)", self.name)
        return super(EvoCallCampaign, self).copy(default=default)

    def action_get_calls(self):
        """ Button action for button box. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Calls',
            'view_mode': 'tree,form,pivot,graph',
            'res_model': 'evo.call',
            'domain': [('campaign_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def start_campaign_out(self):
        self.ensure_one()
        if self.state == 'new':
            self.check_customization()
            self.create_calls()
            self.state = 'go'

    def stop_campaign_out(self):
        if self.state == 'go':
            self.call_ids.stop_call()
            self.state = 'stop'

    def check_customization(self):
        """ Check is custom setting for first message match_pattern: [custom_parameter] """
        if self.start_text:
            matches: List = self.get_key_words()
            for match in matches:
                if match and match not in self.custom_ids.filtered(
                        lambda x: not x.display_type).mapped('name'):
                    raise UserError(_("There is no parameter '%s' in customization") % match)

    def get_key_words(self) -> List[str]:
        match_pattern = r"\[([^\[\]]+)\]"
        matches: List = re.findall(match_pattern, self.start_text)
        return matches

    def get_free_random_number(self) -> models.Model:
        """ Find and return one free number for call. """
        self.ensure_one()
        number_ids = self.number_ids.filtered(lambda x: not x.is_busy)
        if not number_ids:
            return number_ids
        number_id = number_ids[random.randint(0, len(number_ids) - 1)]  # nosec B311
        return number_id

    def create_calls(self):
        """ Create calls after campaign start. """
        call_vals: List[Dict[str, Any]] = []
        for partner_id in self.partner_ids:
            call_dict: Dict[str, Any] = {
                'partner_id': partner_id.id,
                'campaign_id': self.id,
                'call_setting_id': self.call_setting_id.id,
                'state': 'new',
            }
            call_vals.append(call_dict)
        self.env['evo.call'].create(call_vals)

    def finish_campaign(self):
        """ Finish campaign. """
        for rec in self:
            if rec.state == 'go':
                call_in_process_ids = self.env["evo.call"].search([
                    ('campaign_id', '=', rec.id),
                    ('state', 'not in', ['done', 'cancel'])], limit=1)
                if not call_in_process_ids:
                    rec.state = 'stop'

    def pause_campaign(self):
        for rec in self:
            if rec.state == 'go':
                rec.write({'state': 'paused'})

    def unpause_campaign(self):
        for rec in self:
            if rec.state == 'paused':
                rec.write({'state': 'go'})

    def add_related_field(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add related field',
            'view_mode': 'form',
            'res_model': 'evo.call.custom',
            'target': 'new',
            'context': {
                'default_campaign_id': self.id,
                'default_display_type': 'related_record',
            }
        }

    @api.model
    def get_active_campaigns(self) -> models.Model:
        """ Get active companies. """
        return self.env['evo.call.campaign'].search(
            [('state', 'in', ['go', 'paused'])], order='id ASC')
