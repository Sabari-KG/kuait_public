# Copyright 2024 MaiCall
# @author: Ihor Pysmennyi (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
import base64
import ast
import secrets
from typing import Dict, List
from uuid import uuid4
import logging
from datetime import datetime
from pytz import timezone
from dateutil.relativedelta import relativedelta
import requests
from twilio.rest import Client
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from odoo.osv.expression import AND, OR

_logger = logging.getLogger(__name__)


class EvoCall(models.Model):
    _name = 'evo.call'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'EVO Calls'
    _rec_name = 'name'
    _order = "id desc"
    _sql_constraints = [
        ('uuid_unique', 'unique(name)', 'Name must be unique'),
    ]

    name = fields.Char(required=True, readonly=True, copy=False, index=True)
    partner_id = fields.Many2one(
        'res.partner', string="Contact", readonly=True, required=True, index=True)
    campaign_id = fields.Many2one(
        'evo.call.campaign',
        string="Call campaign",
        readonly=True,
        required=True,
        index=True
    )
    call_setting_id = fields.Many2one(
        'evo.call.service.settings', string='Call service', required=True)
    ai_setting_id = fields.Many2one(
        'evo.ai.settings', related='campaign_id.ai_setting_id', store=True)
    number_id = fields.Many2one('evo.call.number', readonly=True)
    call_prompt = fields.Text(readonly=True)
    first_message = fields.Char(readonly=True)
    call_start = fields.Datetime(string="Call Start Time", readonly=True, copy=False)
    call_end = fields.Datetime(string="Call End Time", readonly=True, copy=False)
    call_duration = fields.Float(string="Call Duration (sec)", readonly=True, copy=False)
    call_sid = fields.Char(string="Call SID", readonly=True, copy=False)
    audio_file = fields.Binary(copy=False)
    audio_file_name = fields.Char(readonly=True, copy=False)
    transcription = fields.Text(string="Call Transcription", readonly=True, copy=False)
    transcription_analise = fields.Text(
        string="Call Transcription Analise", readonly=True, copy=False)
    call_cost = fields.Float(
        string="Call Twilio Cost", readonly=True, digits=(16, 4), default=0, copy=False)
    stream_cost = fields.Float(digits=(16, 3), default=0, readonly=True, copy=False)
    record_cost = fields.Float(digits=(16, 4), default=0, readonly=True, copy=False)
    infrastructure_cost = fields.Float(digits=(16, 4), default=0, readonly=True, copy=False)
    ai_cost = fields.Float(digits=(16, 6), default=0, readonly=True, copy=False)
    total_cost = fields.Float(readonly=True, digits=(16, 8), default=0, copy=False)
    code_error = fields.Integer(readonly=True, copy=False)
    audio_url = fields.Char(readonly=True, copy=False)
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('ringing', 'Ringing'),
            ('getting_info', 'Getting Info'),
            ('transcription', 'Transcription'),
            ('analysing', 'Analysing'),
            ('done', 'Done'),
            ('cancel', 'Cancel')
        ],
        default='new',
        required=True,
        tracking=True,
        copy=False,
        help="new - The call is ready and waiting in line before going out.\n"
             "Ringing	- The call is currently ringing.\n"
             "Getting Info	- The call was finished. It's waiting for info.\n"
             "Transcription' - The call is waiting for transcription.\n"
             "Analysing - The call is waiting for analyse.\n"
             "Done - The call has done.\n"
             "Cancel - The call was canceled.\n")
    call_state = fields.Selection(
        selection=[
            ('new', 'New'), ('queued', 'Queued'),
            ('ringing', 'Ringing'),
            ('in-progress', 'In-progress'),
            ('completed', 'Completed'), ('busy', 'Busy'),
            ('failed', 'Failed'), ('no-answer', 'No-answer'),
            ('canceled', 'Canceled')],
        default='new',
        readonly=True,
        required=True,
        copy=False,
        help="Queued - The call is ready and waiting in line before going out.\n"
             "Ringing	- The call is currently ringing.\n"
             "In-progress	- The call was answered and is actively in progress.\n"
             "Completed - The call was answered and has ended normally.\n"
             "Busy - The caller received a busy signal.\n"
             "Failed - The call could not be completed as dialed, "
             "most likely because the phone number was non-existent.\n"
             "No-answer - The call ended without being answered.\n"
             "Canceled - The call was canceled via the REST API while queued or ringing")

    stop_message = fields.Text(readonly=True)
    machine_detected = fields.Boolean(readonly=True, copy=False)
    is_final_call = fields.Boolean(copy=False)
    active = fields.Boolean(default=True)
    evo_call_analysis_ids = fields.One2many('evo.call.analysis', 'call_id')
    download_token = fields.Char(readonly=True)
    download_link = fields.Char(readonly=True, compute="_compute_download_link", store=True)
    custom_related_data_ids = fields.One2many(
        'evo.call.custom.related.data',
        'call_id',
        string="Custom related data")

    def unlink(self):
        for record in self:
            if record.state != "new":
                raise ValidationError(_("You cannot delete a call with this status."))
        return super(EvoCall, self).unlink()

    @api.depends('audio_file')
    def _compute_download_link(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            if record.audio_file and record.download_token:
                record.download_link = base_url + '/public/download/' + record.download_token
            else:
                record.download_link = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = str(uuid4())
            if "download_token" not in vals:
                key = secrets.token_urlsafe(32)
                vals["download_token"] = key
        return super(EvoCall, self).create(vals_list)

    def action_get_call_analysis(self):
        """ Button action for button box. """

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Call analysis',
            'view_mode': 'tree,form',
            'res_model': 'evo.call.analysis',
            'domain': [('call_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_get_call_related_data(self):
        """ Button action for button box. """

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Call analysis',
            'view_mode': 'tree',
            'res_model': 'evo.call.custom.related.data',
            'domain': [('call_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def stop_call(self):
        """ Stop button """
        for record in self:
            if record.state == 'new':
                record.state = 'cancel'

    def get_transcription(self):
        """ Get info, redial and finish campaign. self - calls from one campaign. """
        for record in self:
            write_dict: Dict = {'state': 'analysing'}
            record.write(write_dict)
            record.check_and_run_redial()

    def run_analysis(self):
        self.write({'state': 'done'})
        self.campaign_id.finish_campaign()

    def check_and_run_redial(self):
        """ This method is replaced in module evo_ai_call_redial. """
        self.write({'is_final_call': True})

    def add_criteria_for_domain(
            self, search_domain: List, criteria_condition: str, criteria_domain: str,
            by_campaign: bool = False):
        """ Add filter domain based on criteria conditions. """
        if not criteria_domain or criteria_domain == '[]':
            return search_domain

        criteria_search_domain = AND([
            [('call_id', '=', self.id)] if not by_campaign else [
                ('campaign_id', 'in', self.campaign_id.ids)],
            ast.literal_eval(criteria_domain)
        ])
        criteria_ids = self.env["evo.call.analysis"].search(criteria_search_domain)
        if not criteria_ids:
            return search_domain if criteria_condition != 'and' else False

        operator = AND if criteria_condition == 'and' else OR
        return operator([search_domain, [('id', 'in', criteria_ids.call_id.ids)]])

    def get_call_info(self):
        """ Get call info from services. self - calls from one company. """
        call_setting_id = self.mapped('call_setting_id')
        try:
            twilio_client: Client = Client(call_setting_id.account_sid, call_setting_id.auth_token)
            for record in self:
                if not record.call_sid:
                    record.write({'state': 'transcription'})
                    continue
                # take information about call
                try:
                    call_details = twilio_client.calls(record.call_sid).fetch()
                    write_dict: Dict = {
                        'call_state': call_details.status,
                        'call_start': call_details.start_time.replace(
                            tzinfo=None) if call_details.start_time else None,
                        'call_end': call_details.end_time.replace(
                            tzinfo=None) if call_details.end_time else None,
                        'call_duration': call_details.duration,
                        'call_cost': abs(
                            float(call_details.price if call_details.price else 0.0)),
                        'state': 'transcription'
                    }
                    _logger.info(
                        "Get call data from twilio. Call name: %(name)s. Cost: %(cost)s", {
                            'name': record.name,
                            'cost': call_details.price,
                        })
                    record.write(write_dict)
                    record.calculate_expenses()
                except Exception as e:
                    _logger.error(
                        "Get call data from twilio. Call name: %(name)s. %(error)s", {
                            'name': record.name,
                            'error': e
                        })
            call_ids = self.filtered(lambda x: x.call_sid)
            if call_ids:
                call_ids.get_audio()
        except Exception as e:
            _logger.error(
                "Get call data from twilio. Call settings: %(settings)s. %(error)s", {
                    'settings': call_setting_id.name,
                    'error': e
                })

    def get_audio(self):
        """ Get audio. """
        try:
            if not self:
                return
            call_setting_id = self.mapped('call_setting_id')
            twilio_client: Client = Client(call_setting_id.account_sid, call_setting_id.auth_token)
        except Exception as e:
            _logger.error('Error getting audio: %s', e)
        else:
            for record in self:
                write_dict: Dict = {'audio_file_name': record.call_sid + '.mp3'}
                audio_payload = record.get_twilio_audio(client=twilio_client)
                if audio_payload:
                    write_dict['audio_file'] = audio_payload
                    write_dict['audio_url'] = 'twilio'
                record.write(write_dict)

    def get_twilio_audio(self, client: Client):
        """ Get audio content from Twilio. encode into base64 """
        if self.call_sid and self.call_setting_id.record_call:
            try:
                recordings = client.recordings.list(call_sid=self.call_sid)
                if recordings:
                    recording_url = ("https://api.twilio.com%s" % recordings[
                        0].uri.replace('.json', '.mp3'))
                    response = requests.get(
                        recording_url, auth=(client.username, client.password), timeout=30)
                    if response.status_code == 200:
                        # audio record
                        return base64.b64encode(response.content) if response.content else None
            except Exception as e:
                _logger.error(e)
        return None

    def calculate_expenses(self):
        """ Calculate call expenses. """
        write_dict = self.get_calculate_dict()
        self.write(write_dict)

    def get_calculate_dict(self):
        write_dict: dict = {}
        call_duration_minutes: float = round(self.call_duration / 60, 2)
        stream_cost = self.call_setting_id.stream_cost * call_duration_minutes
        record_cost = self.call_setting_id.record_cost * call_duration_minutes
        if_cost = self.call_setting_id.infrastructure_cost * call_duration_minutes
        ai_cost = self.ai_setting_id.cost * call_duration_minutes
        write_dict.update({
            'ai_cost': ai_cost,
            'total_cost': ai_cost + stream_cost + record_cost + if_cost,
            'stream_cost': stream_cost,
            'record_cost': record_cost,
            'infrastructure_cost': if_cost})
        return write_dict

    @api.model
    def _cron_get_info(self, limit=20):
        """ Cron gets info from call service. """
        self.run_cron_job(limit=limit, state='getting_info')

    @api.model
    def _cron_get_transcription(self, limit=20):
        self.run_cron_job(limit=limit, state='transcription')

    @api.model
    def _cron_analyse(self, limit=20):
        self.run_cron_job(limit=limit, state='analysing')

    @api.model
    def run_cron_job(self, limit: int, state: str):
        for campaign_id in self.env['evo.call.campaign'].get_active_campaigns():
            domain_info = [
                ('state', '=', state),
                ('campaign_id', '=', campaign_id.id)
            ]
            if state == 'getting_info':
                domain_info.append(
                    ('write_date', '<', fields.Datetime.now() - relativedelta(minutes=2)))
            if limit > 0:
                call_ids = self.search(domain_info, limit=limit)
                if call_ids:
                    limit -= len(call_ids)
                    if state == 'getting_info':
                        call_ids.get_call_info()
                    elif state == 'transcription':
                        call_ids.get_transcription()
                    elif state == 'analysing':
                        call_ids.run_analysis()

    def update_partner_last_call_date(self):
        """ Compute and write into partner call time. It's for prompt customization. """
        for record in self:
            record.partner_id.last_call_date = datetime.now().date()

    def get_time_zone(self):
        tz = self.env.company.partner_id.tz
        if tz:
            return timezone(tz)
        return False

    # pylint: disable=too-many-branches
    def generate_custom_prompt_and_message(self):
        """ Generate custom message and prompt for call. """
        self.ensure_one()
        tz = self.get_time_zone()
        campaign_id = self.campaign_id
        partner_id = self.partner_id

        key_words: List = campaign_id.get_key_words()
        custom_ids = campaign_id.custom_ids
        message_custom_ids = custom_ids.filtered(
            lambda x: not x.display_type and x.name in key_words)
        first_message: str = campaign_id.start_text
        add_prompt: List = [campaign_id.prompt]
        for message_custom_id in message_custom_ids:
            value = message_custom_id.prepare_field_char_value(
                message_custom_id.field_char, partner_id, tz)
            if value is None:
                continue
            first_message: str = first_message.replace(
                f"[{message_custom_id.name}]", value)

        related_models_data = []
        for custom_id in custom_ids:
            if custom_id.display_type == "line_section":
                add_prompt.append("\n-----------------------")
                add_prompt.append(f"#### {custom_id.name}: ")

            elif not custom_id.display_type:
                value = custom_id.prepare_field_char_value(custom_id.field_char, partner_id, tz)
                if value is None:
                    continue
                add_prompt.append(
                    f"- {custom_id.name}: {str(value)}")

            elif custom_id.display_type == "related_record":
                if custom_id.domain_related:
                    domain_related = ast.literal_eval(custom_id.domain_related)
                    domain_related.append((f"{custom_id.related_field_id.name}",
                                           "=",
                                           partner_id.id))
                    record_ids = self.env[custom_id.model_id.model].search(domain_related)
                else:
                    domain_related = [(f"{custom_id.related_field_id.name}",
                                       "=",
                                       partner_id.id)]
                    record_ids = self.env[custom_id.model_id.model].search(domain_related)
                for index, record in enumerate(record_ids):
                    r_data = {
                        'model_name': record._name,
                        'rec_id': record.id,
                        'call_id': self.id,
                    }
                    related_models_data.append(r_data)
                    add_prompt.append(
                        f"{custom_id.name} {index+1}:")
                    for rel in custom_id.custom_related_ids:
                        info = rel.prepare_field_char_value(rel.field_char, record, tz)
                        if info is None:
                            continue
                        add_prompt.append(
                            f"- {rel.name} : {info}")
        if related_models_data:
            self.env['evo.call.custom.related.data'].create(related_models_data)

        self.write({
            'call_prompt': "\n".join(add_prompt),
            'first_message': first_message
        })

    def run_calls(self):
        """ Initiate call on call service. """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            _logger.info("Run call: %s", record.name)
            number_id: models.Model = record.campaign_id.get_free_random_number()
            if record.campaign_id.state != 'go' or not number_id:
                continue
            record.update_partner_last_call_date()
            record.generate_custom_prompt_and_message()
            record.number_id = number_id.id

            header: Dict = {"Authorization": record.call_setting_id.api_key}
            params: Dict = record.get_call_params(base_url=base_url, number=number_id.name)
            # RUN call if it has AI parameters
            if params.get('ai_parameters', {}):
                resp = requests.post(
                    url=f"{record.call_setting_id.call_url}/v1/create-call",
                    headers=header,
                    json=params,
                    timeout=10.0,
                )
                if resp.status_code != 200:
                    _logger.error(resp.text)
                    raise ValidationError(resp.text)
                resp_message = resp.json()
                if resp_message.get('status_code', 0) != 200:
                    response_code = resp_message.get('code', 0)
                    if response_code in [20003, 20101, 400]:
                        record.campaign_id.pause_campaign()
                        record.campaign_id.message_post(body=resp_message.get('message', ''))
                        break
                    else:
                        record.write({'state': 'done', 'code_error': response_code})
                        record.campaign_id.finish_campaign()
                        continue
                record.write({
                    'state': 'ringing',
                    'call_sid': resp_message['call_sid'],
                })
                number_id.write({'is_busy': True})
            else:
                record.write({'state': 'ringing'})

    def get_call_params(self, base_url, number) -> Dict:
        """ Prepare parameters for call. """
        self.ensure_one()
        call_setting_id = self.call_setting_id
        params: Dict = {
            'name': self.name,
            'to': self.partner_id.mobile,
            'from_': number,
            'time_limit': call_setting_id.call_time_limit,
            'account_sid': call_setting_id.account_sid,
            'twilio_token': call_setting_id.auth_token,
            'machine_detection': call_setting_id.machine_detection,
            'record_call': call_setting_id.record_call,
            'state': 'new',
            'state_callback_url': base_url,
        }
        return params
