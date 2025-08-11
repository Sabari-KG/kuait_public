# Copyright 2024 MaiCall
# @author: Ihor Pysmennyi (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
from odoo import models, fields, api


class EvoCallCustom(models.Model):
    _name = 'evo.call.custom'
    _description = 'EVO Call Custom'
    _order = "sequence, id desc"
    _sql_constraints = [
        ('name_unique', 'unique(name, campaign_id)', 'Name and campaign must be unique.'),
    ]

    name = fields.Char(required=True)
    campaign_id = fields.Many2one('evo.call.campaign', required=True, ondelete='cascade')
    sequence = fields.Integer(default=1)
    field_id = fields.Many2one(
        'ir.model.fields',
        ondelete='cascade',
        domain="[('model', '=', 'res.partner')]")
    field_char = fields.Char("Field")
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
            ('related_record', "Related"),
        ],
        default=False
    )
    related_field = fields.Html(readonly=True,
                                compute="_compute_related_field_name",
                                store=True)
    related_field_id = fields.Many2one(
        'ir.model.fields',
        ondelete="cascade",
        help="A field that links the selected model to the Contact model.",
        domain="[('model_id', '=', model_id),('relation', '=', 'res.partner')]"
    )
    domain_related = fields.Char(
        default=False,
        help="Specify the conditions that the records of the selected "
             "model must satisfy. Only the selected records will contain "
             "data for the prompt.",
    )
    model_id = fields.Many2one(
        'ir.model',
        ondelete="cascade",
        help="The model associated with the Contact from which you need to take data.",
        default=lambda self: self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
    )
    model = fields.Char(related="model_id.model")
    custom_related_ids = fields.One2many(
        'evo.call.custom.related',
        'evo_call_custom_id',
        string='Related Customizations',
        copy=True)

    @api.depends('custom_related_ids')
    def _compute_related_field_name(self):
        for record in self:
            text = ''
            if record.custom_related_ids:
                for rel in record.custom_related_ids:
                    field = self.env['ir.model.fields'].search([('model_id',
                                                                 '=',
                                                                 record.model_id.id),
                                                                ('name',
                                                                 '=',
                                                                 rel.field_char)])

                    if field:
                        field_name = field.field_description
                    else:
                        field_name = rel.field_char

                    text += (f"<div>{rel.name}: {field_name} "
                             f"({record.model_id.name})</div></br>")
                record.related_field = text
            else:
                record.related_field = False

    def edit_custom_related_field(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit related field',
            'view_mode': 'form',
            'res_model': 'evo.call.custom',
            'target': 'new',
            'res_id': self.id,
        }
