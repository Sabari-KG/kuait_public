# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, fields, models,_
from datetime import timedelta,datetime
from dateutil.relativedelta import relativedelta
import calendar

_logger = logging.getLogger(__name__)


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"


    buffer_days = fields.Integer(string="Buffer Days")
    reorder_update_id = fields.Many2one('reorder.update.config')

    # get first, last & month of last month
    def get_current_last_month(self):
        today = datetime.today()
        first_day_this_month = today.replace(day=1)
        last_month = first_day_this_month - relativedelta(months=1)
        first_day_last_month = first_day_this_month - relativedelta(months=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        return first_day_last_month, last_day_last_month,last_month

    # get total days of last month
    def get_days_in_month(self,year, month):
        return calendar.monthrange(year, month)[1]

    # get first, last & month of last month(given)
    def get_avg_last_month(self, last_months):
        average_month_days = 0
        today = datetime.today()
        first_day_this_month = today.replace(day=1)
        last_month = first_day_this_month - relativedelta(months=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        for i in range(1, (int(last_months)) + 1):
            avg_month = first_day_this_month - relativedelta(months=i)
            avg_month_days = self.get_days_in_month(avg_month.year, avg_month.month)
            average_month_days += avg_month_days
            if i == int(last_months):
                first_month = first_day_this_month - relativedelta(months=i)
                first_day_first_month = first_day_this_month - relativedelta(months=i)
        return first_day_first_month, last_day_last_month, average_month_days

    # get seasonal sales avg qty
    def get_seasonal_sale_qty(self, delay, reordering):
        today = datetime.today()
        current_year = today.year
        current_month = today.month
        previous_year = current_year - 1
        same_day_last_year = today - relativedelta(years=1)
        delay_days_date = same_day_last_year + timedelta(days=delay)
        last_year_same_month = same_day_last_year.replace(hour=0, minute=0, second=0)
        delay_days_end_date = delay_days_date.replace(hour=23, minute=59, second=59)
        sale_lines = self.env['sale.order.line'].search([
            ('order_id.date_order', '>=', last_year_same_month),
            ('order_id.date_order', '<=', delay_days_end_date),
            ('product_id', '=', reordering.product_id.id),
            ('order_id.state', '=', ['sale'])])
        pos_lines = self.env['pos.order.line'].search([
            ('order_id.date_order', '>=', last_year_same_month),
            ('order_id.date_order', '<=', delay_days_end_date),
            ('product_id', '=', reordering.product_id.id),
            ('order_id.state', 'in', ['paid', 'done', 'invoiced'])])
        total_qty =0
        if sale_lines:
            total_qty = sum(line.product_uom_qty for line in sale_lines)
        if pos_lines:
            total_qty += sum(line.qty for line in pos_lines)
        if sale_lines or pos_lines:
            avg_sale_qty = total_qty / delay
            return avg_sale_qty
        else:
            return 1

    # monthly based sales
    def get_monthly_reordering(self, reorderings):
        last_month_data = self.get_current_last_month()
        for reordering in reorderings:
            last_month_start_date = last_month_data[0].replace(hour=0, minute=0, second=0)
            last_month_end_date = last_month_data[1].replace(hour=23, minute=59, second=59)
            sale_lines = self.env['sale.order.line'].search([
                ('order_id.date_order', '>=', last_month_start_date),
                ('order_id.date_order', '<=', last_month_end_date),
                ('product_id', '=', reordering.product_id.id),
                ('order_id.state', '=', 'sale')])
            total_qty = sum(line.product_uom_qty for line in sale_lines)
            pos_lines = self.env['pos.order.line'].search([
                ('order_id.date_order', '>=', last_month_start_date),
                ('order_id.date_order', '<=', last_month_end_date),
                ('product_id', '=', reordering.product_id.id),
                ('order_id.state', 'in', ['paid','done','invoiced'])])
            total_qty += sum(line.qty for line in pos_lines)
            total_days = self.get_days_in_month(last_month_data[2].year, last_month_data[2].month)
            avg_sale_qty = total_qty / total_days
            delay = 0
            seasonal_sale_setting = self.env['ir.config_parameter'].sudo().get_param(
                'kp_auto_reordering.is_include_seasonal_sale')
            if reordering.supplier_id:
                vendor_data = reordering.product_id.seller_ids.filtered(lambda s: s.id == reordering.supplier_id.id)
                delay = vendor_data[0].delay
            else:
                delay = reordering.product_id.seller_ids[0].delay if reordering.product_id.seller_ids else 0
            if seasonal_sale_setting:
                delay = self.get_seasonal_sale_qty(delay, reordering)
            reordering.product_min_qty = avg_sale_qty * delay
            reordering.product_max_qty = (avg_sale_qty * delay) + reordering.buffer_days

    # Average based sales
    def get_average_reordering(self, reorderings):
        last_months = self.env['ir.config_parameter'].sudo().get_param('kp_auto_reordering.sale_qty_avg_month')
        avg_month_data = self.get_avg_last_month(last_months)
        for reordering in reorderings:
            avg_month_start_date = avg_month_data[0].replace(hour=0, minute=0, second=0)
            avg_month_end_date = avg_month_data[1].replace(hour=23, minute=59, second=59)
            sale_lines = self.env['sale.order.line'].search([
                ('order_id.date_order', '>=', avg_month_start_date),
                ('order_id.date_order', '<=', avg_month_end_date),
                ('product_id', '=', reordering.product_id.id),
                ('order_id.state', '=', ['sale'])])
            total_qty = sum(line.product_uom_qty for line in sale_lines)
            pos_lines = self.env['pos.order.line'].search([
                ('order_id.date_order', '>=', avg_month_start_date),
                ('order_id.date_order', '<=', avg_month_end_date),
                ('product_id', '=', reordering.product_id.id),
                ('order_id.state', 'in', ['paid', 'done', 'invoiced'])])
            total_qty += sum(line.qty for line in pos_lines)
            total_days = avg_month_data[2]
            avg_sale_qty = total_qty / total_days
            delay = 0
            seasonal_sale_setting = self.env['ir.config_parameter'].sudo().get_param(
                'kp_auto_reordering.is_include_seasonal_sale')
            if reordering.supplier_id:
                vendor_data = reordering.product_id.seller_ids.filtered(lambda s: s.id == reordering.supplier_id.id)
                delay = vendor_data[0].delay
            else:
                delay = reordering.product_id.seller_ids[0].delay if reordering.product_id.seller_ids else 0
            if seasonal_sale_setting:
                delay = self.get_seasonal_sale_qty(delay, reordering)
            reordering.product_min_qty = avg_sale_qty * delay
            reordering.product_max_qty = (avg_sale_qty * delay) + reordering.buffer_days

    def update_reorder_min_max(self):
        reorderings = self.env['stock.warehouse.orderpoint'].sudo().search([('product_id', '=',4310)])
        sale_qty_methods = self.env['ir.config_parameter'].sudo().get_param('kp_auto_reordering.sale_qty_method')
        if sale_qty_methods == 'Monthly':
            monthly_reordering = self.get_monthly_reordering(reorderings)
        if sale_qty_methods == 'Average':
            average_reordering = self.get_average_reordering(reorderings)


