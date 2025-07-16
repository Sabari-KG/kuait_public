from odoo import models, fields, api
from datetime import datetime,timedelta, date
from dateutil.relativedelta import relativedelta
import calendar

class ReorderHistory(models.Model):
    _name = 'reorder.history'
    _description = 'Reorder Update Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    reorder_update_id = fields.Many2one('reorder.update.config',tracking=True)
    product_id = fields.Many2one('product.product', string='Products')
    reordering_id = fields.Many2one('stock.warehouse.orderpoint',tracking=True)
    line_ids = fields.One2many('reorder.history.line', 'history_id')


class ReorderHistoryLine(models.Model):
    _name = 'reorder.history.line'

    history_id = fields.Many2one('reorder.history')
    history_date = fields.Date(string="Date")
    product_min_qty = fields.Float('Min Quantity', digits='Product Unit of Measure')
    product_max_qty = fields.Float('Max Quantity', digits='Product Unit of Measure')

