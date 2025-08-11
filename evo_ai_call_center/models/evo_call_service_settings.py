# Copyright 2024 MaiCall
# @author: Ihor Pysmennyi (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
import logging
from datetime import timedelta, datetime
from typing import List
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class EvoCallServiceSettings(models.Model):
    _name = 'evo.call.service.settings'
    _description = 'Call service settings'

    name = fields.Char(required=True)
    service_type = fields.Selection([('twilio', 'Twilio')], required=True, default="twilio")
    account_sid = fields.Char(string="Account SID", required=True)
    auth_token = fields.Char(required=True)
    call_time_limit = fields.Integer(required=True, default=900)
    call_url = fields.Char(string='Uvicorn URL', required=True)
    api_key = fields.Char(string="Uvicorn API Key", required=True)
    stream_cost = fields.Float(default=0.004, digits=(16, 3), required=True)
    record_cost = fields.Float(default=0.0025, digits=(16, 4), required=True)
    infrastructure_cost = fields.Float(
        help="Cost for 1 minute of call.", default=0.0001, digits=(16, 4), required=True)
    active = fields.Boolean(default=True)
    number_ids = fields.One2many('evo.call.number', 'service_id')
    machine_detection = fields.Boolean(default=False)
    record_call = fields.Boolean(default=False)

    def action_get_call_numbers(self):
        """ Button action for button box. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Call numbers',
            'view_mode': 'tree,form',
            'res_model': 'evo.call.number',
            'domain': [('service_id', '=', self.id)],
            'context': {'default_service_id': self.id}
        }

    @api.model
    def _cron_run_calls(self):
        """ Run new calls by schedule. """
        active_campaign_ids = self.env['evo.call.campaign'].search([('state', '=', 'go')])
        for record in self.search([]):
            record.finish_busy_calls()
            call_domain: List = record.get_call_domain(active_campaign_ids=active_campaign_ids)
            record.run_service_calls(call_domain=call_domain)

    def finish_busy_calls(self):
        """ Finish busy calls, which are not finished ontime. """
        self.ensure_one()
        active_call_ids = self.env['evo.call'].search([
            ('call_setting_id', '=', self.id),
            ('state', '=', 'ringing'),
        ], limit=100)
        call_time_limit: int = self.call_time_limit + 20  # + 20 sec
        for active_call_id in active_call_ids:
            end_time = active_call_id.write_date + timedelta(seconds=call_time_limit)
            if end_time <= datetime.now():
                if active_call_id.ai_setting_id.service_type == 'unknown':
                    active_call_id.write({
                        'state': 'getting_info',
                        'stop_message': 'There is no AI service.'
                    })
                    active_call_id.number_id.write({'is_busy': False})
                    continue

                active_call_id.write({
                    'state': 'cancel',
                    'stop_message': 'Call is stopped by odoo.'
                })
                active_call_id.check_and_run_redial()
                active_call_id.number_id.write({'is_busy': False})
                active_call_id.campaign_id.finish_campaign()

    def get_call_domain(self, active_campaign_ids) -> List:
        """ Get domain for new calls. """
        call_domain: List = [
            ('campaign_id', 'in', active_campaign_ids.ids),
            ('call_setting_id', '=', self.id),
            ('state', '=', 'new'),
        ]
        return call_domain

    def run_service_calls(self, call_domain: List) -> models.Model:
        """ Run new calls. """
        self.ensure_one()
        new_call_ids = self.env['evo.call'].search(call_domain, limit=30, order='id asc')
        new_call_ids.run_calls()
        return new_call_ids
