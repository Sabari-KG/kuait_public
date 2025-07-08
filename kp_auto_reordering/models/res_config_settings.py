# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_qty_method = fields.Selection([('Monthly', 'Monthly'),('Average', 'Average')], string='Sales Quantity Method',
                                       config_parameter='kp_auto_reordering.sale_qty_method')

    sale_qty_avg_month = fields.Integer(string='Months',config_parameter='kp_auto_reordering.sale_qty_avg_month')
