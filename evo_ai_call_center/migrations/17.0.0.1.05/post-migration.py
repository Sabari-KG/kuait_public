
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    res_partner_model = env['ir.model'].search([('model', '=', 'res.partner')], limit=1)

    calls_to_update = env['evo.call.custom'].search([('display_type', '=', False)])

    for call in calls_to_update:
        call.model_id = res_partner_model.id
