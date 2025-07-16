from odoo import models, fields, api
from datetime import datetime,timedelta, date
from dateutil.relativedelta import relativedelta
import calendar

class ReorderUpdateConfig(models.Model):
    _name = 'reorder.update.config'
    _description = 'Reorder Update Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Configuration Name', required=True)
    apply_on = fields.Selection([
        ('product', 'Product'),
        ('category', 'Product Category'),
        ('warehouse', 'Warehouse')
    ], string='Apply On', required=True,tracking=True)
    product_ids = fields.Many2many('product.product', string='Products')
    category_id = fields.Many2one('product.category', string='Category')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    update_method = fields.Selection([
        ('monthly', 'Monthly'),
        ('every_x_days', 'Every X Days')
    ], string='Update Method', required=True,tracking=True)
    x_days = fields.Integer(string='X Days',tracking=True)
    start_date = fields.Date(string='Start Date', default=fields.Date.today)
    lead_time_source = fields.Selection([
        ('supplier_lead', 'Supplier Lead Time'),
        ('fixed_lead_days', 'Fixed Lead Days')
    ], string='Lead Time Source', required=True,tracking=True)
    fixed_lead_days = fields.Integer(string='Fixed Lead Days',tracking=True)
    buffer_percentage = fields.Float(string='Buffer Percentage',tracking=True)
    use_previous_year_data = fields.Boolean(string='Use Previous Year Data')
    previous_years_count = fields.Integer(string='Previous Years Count')
    active = fields.Boolean(default=True)
    next_run_date = fields.Date(tracking=True)
    state = fields.Selection([
        ('new', 'New'),
        ('active', 'Active'),
        ('cancelled', 'Cancelled')], default='new',tracking=True)
    sale_qty_method = fields.Selection([('Monthly', 'Monthly'), ('Average', 'Average')], string='Sales Quantity Method',tracking=True)
    sale_qty_avg_month = fields.Integer(string='Months',tracking=True)
    reordering_line_ids = fields.Many2many('stock.warehouse.orderpoint')
    is_confirmed = fields.Boolean(string="Active")
    sale_qty_avg_month = fields.Integer(string='Last Months', default="1")


    @api.onchange('update_method', 'x_days')
    def onchange_update_method(self):
        for rec in self:
            if rec.update_method == 'monthly' and rec.next_run_date and rec.state == 'active':
                rec.next_run_date = rec.next_run_date + relativedelta(months=1)
            if rec.update_method == 'every_x_days' and rec.next_run_date and rec.x_days and rec.state == 'active':
                rec.next_run_date = rec.next_run_date + timedelta(days=rec.x_days)


    def create_reorder(self,product):
        for rec in self:
            vals = {
                'product_id': product.id,
                'reorder_update_id': rec.id
            }
            reorder = self.env['stock.warehouse.orderpoint'].sudo().create(vals)
            if rec.lead_time_source == 'fixed_lead_days' and rec.fixed_lead_days and product.seller_ids:
                product.seller_ids[0].delay = rec.fixed_lead_days
            rec.reordering_line_ids = [(4, reorder.id)]
            return reorder

    # To create reorder when confirm reorder config
    def create_product_reorder(self):
        for rec in self:
            reorderings = self.env['stock.warehouse.orderpoint'].sudo().search([])
            if reorderings:
                reordering_pdts = reorderings.mapped('product_id')
            if rec.apply_on == 'product' and rec.product_ids:
                for product_id in rec.product_ids:
                    if product_id not in reordering_pdts:
                        rec.create_reorder(product_id)
                    if product_id in reordering_pdts:
                        reorderings = self.env['stock.warehouse.orderpoint'].sudo().search([('product_id','=',product_id.id)],limit=1)
                        reorderings.reorder_update_id = rec.id
                        rec.reordering_line_ids = [(4,reorderings.id)]
                        if rec.lead_time_source == 'fixed_lead_days' and rec.fixed_lead_days and product_id.seller_ids:
                            product_id.seller_ids[0].delay = rec.fixed_lead_days
            if rec.apply_on == 'category' and rec.category_id:
                catrgory_ids = self.env['product.category'].search(['|',('id','=', rec.category_id.id),('parent_id','=', rec.category_id.id)])
                category_products = self.env['product.product'].search([('categ_id', 'in', catrgory_ids.ids)])
                for category_product in category_products:
                    if category_product not in reordering_pdts:
                        rec.create_reorder(category_product)
                    if category_product in reordering_pdts:
                        reorderings = self.env['stock.warehouse.orderpoint'].sudo().search([('product_id','=',category_product.id)],limit=1)
                        reorderings.reorder_update_id = rec.id
                        rec.reordering_line_ids = [(4,reorderings.id)]
                        if rec.lead_time_source == 'fixed_lead_days' and rec.fixed_lead_days and category_product.seller_ids:
                            category_product.seller_ids[0].delay = rec.fixed_lead_days
            if rec.apply_on == 'warehouse' and rec.warehouse_id:
                locations = self.env['stock.location'].search([('warehouse_id', '=', rec.warehouse_id.id), ('usage', '=', 'internal')])
                quants = self.env['stock.quant'].search([('location_id', 'in', locations.ids)])
                warehouse_pdts = quants.mapped('product_id')
                for warehouse_pdt in warehouse_pdts:
                    if warehouse_pdt not in reordering_pdts:
                        rec.create_reorder(warehouse_pdt)
                    if warehouse_pdt in reordering_pdts:
                        reorderings = self.env['stock.warehouse.orderpoint'].sudo().search([('product_id','=',warehouse_pdt.id)],limit=1)
                        reorderings.reorder_update_id = rec.id
                        rec.reordering_line_ids = [(4,reorderings.id)]
                        if rec.lead_time_source == 'fixed_lead_days' and rec.fixed_lead_days and warehouse_pdt.seller_ids:
                            warehouse_pdt.seller_ids[0].delay = rec.fixed_lead_days

    def update_confirm_next_run_date(self):
        for rec in self:
            if rec.update_method == 'monthly' and rec.start_date and rec.state == 'active':
                rec.next_run_date = rec.start_date+relativedelta(months=1)
            if rec.update_method == 'every_x_days' and rec.start_date and rec.x_days and rec.state == 'active':
                rec.next_run_date = rec.start_date + timedelta(days=rec.x_days)


    def action_confirm(self):
        for rec in self:
            reorder = rec.create_product_reorder()
            rec.write({'state': 'active', 'is_confirmed': True})
            rec.update_confirm_next_run_date()

    def action_cancel_reorder_config(self):
        for rec in self:
            rec.write({'state': 'cancelled', 'is_confirmed':False})


    def create_update_reorder_history(self, reordering, reorder_config,history_pdts, min_qty, max_qty):
        for rec in reorder_config:
            if reordering.product_id in history_pdts:
                reorder_history = self.env['reorder.history'].search([('product_id', '=', reordering.product_id.id)],limit=1)
                if reorder_history:
                    reorder_history.write({
                                           'reorder_update_id': rec.id,
                                           'reordering_id': reordering.id,
                                           'line_ids': [(0, 0, {'product_max_qty': max_qty,
                                                                'product_min_qty': min_qty,
                                                                'history_date': fields.Date.today(),
                                                                'history_id': reorder_history.id
                                                                })]
                                           })
            else:
                vals = {
                        'product_id': reordering.product_id.id,
                        'reordering_id': reordering.id,
                        'reorder_update_id': rec.id,
                        'line_ids': [(0,0, {'product_max_qty': max_qty,
                        'product_min_qty': min_qty,
                        'history_date': fields.Date.today(),})]
                       }

                self.env['reorder.history'].create(vals)


    def get_current_last_month(self):
        current_date_time = datetime.now()
        last_month_date = datetime.today() - timedelta(days=30)
        return last_month_date,current_date_time

    # get total days of last month
    def get_days_in_month(self, year, month):
        return calendar.monthrange(year, month)[1]

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
        total_qty = 0
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
    def get_monthly_reordering(self, reorder_config, reorderings):
        last_month_data = self.get_current_last_month()
        history_pdts = self.env['reorder.history'].search([]).mapped('product_id')
        for reordering in reorderings:
            last_month_start_date = last_month_data[0].replace(hour=0, minute=0, second=0)
            current_month_date = last_month_data[1].replace(hour=23, minute=59, second=59)
            sale_lines = self.env['sale.order.line'].search([
                ('order_id.date_order', '>=', last_month_start_date),
                ('order_id.date_order', '<=', current_month_date),
                ('product_id', '=', reordering.product_id.id),
                ('order_id.state', '=', 'sale')])
            total_qty = sum(line.product_uom_qty for line in sale_lines)
            pos_lines = self.env['pos.order.line'].search([
                ('order_id.date_order', '>=', last_month_start_date),
                ('order_id.date_order', '<=', current_month_date),
                ('product_id', '=', reordering.product_id.id),
                ('order_id.state', 'in', ['paid', 'done', 'invoiced'])])
            total_qty += sum(line.qty for line in pos_lines)
            total_days = (last_month_data[1] - last_month_data[0]).days+1
            avg_sale_qty = total_qty / total_days
            delay = 0
            seasonal_sale_setting = reorder_config.use_previous_year_data
            if reordering.supplier_id:
                vendor_data = reordering.product_id.seller_ids.filtered(lambda s: s.id == reordering.supplier_id.id)
                delay = vendor_data[0].delay
            else:
                delay = reordering.product_id.seller_ids[0].delay if reordering.product_id.seller_ids else 0
            if seasonal_sale_setting:
                delay = self.get_seasonal_sale_qty(delay, reordering)
            reordering.product_min_qty = avg_sale_qty * delay
            reordering.product_max_qty = (avg_sale_qty * delay) + (1+reorder_config.buffer_percentage/100)
            self.create_update_reorder_history(reordering, reorder_config,history_pdts,reordering.product_min_qty, reordering.product_max_qty)

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

    # Average based sales
    def get_average_reordering(self, reorder_config, reorderings):
        last_months = reorder_config.sale_qty_avg_month
        avg_month_data = self.get_avg_last_month(last_months)
        history_pdts = self.env['reorder.history'].search([]).mapped('product_id')
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
            seasonal_sale_setting = reorder_config.use_previous_year_data
            if reordering.supplier_id:
                vendor_data = reordering.product_id.seller_ids.filtered(lambda s: s.id == reordering.supplier_id.id)
                delay = vendor_data[0].delay
            else:
                delay = reordering.product_id.seller_ids[0].delay if reordering.product_id.seller_ids else 0
            if seasonal_sale_setting:
                delay = self.get_seasonal_sale_qty(delay, reordering)
            reordering.product_min_qty = avg_sale_qty * delay
            reordering.product_max_qty = (avg_sale_qty * delay) + (1+reorder_config.buffer_percentage/100)
            self.create_update_reorder_history(reordering, reorder_config, history_pdts, reordering.product_min_qty,
                                               reordering.product_max_qty)

    def update_next_run_date(self,reorder_config):
        if reorder_config.update_method == 'monthly' and reorder_config.next_run_date and reorder_config.state == 'active':
            reorder_config.next_run_date = reorder_config.next_run_date+relativedelta(months=1)
        if reorder_config.update_method == 'every_x_days' and reorder_config.start_date and reorder_config.x_days and reorder_config.state == 'active':
            reorder_config.next_run_date = reorder_config.next_run_date + timedelta(days=reorder_config.x_days)


    def update_config_reorder_min_max(self):
        reorder_configs = self.env['reorder.update.config'].sudo().search([('is_confirmed', '=', True),
                                                                       ('state', '=', 'active'),
                                                                       ('start_date','<=', date.today()),
                                                                       ('next_run_date','=', date.today())])
        for reorder_config in reorder_configs:
            if reorder_config.sale_qty_method == 'Monthly':
                monthly_reordering = self.get_monthly_reordering(reorder_config,reorder_config.reordering_line_ids)
                reorder_config.update_next_run_date(reorder_config)

            if reorder_config.sale_qty_method == 'Average' and reorder_config.sale_qty_avg_month>0:
                monthly_reordering = self.get_average_reordering(reorder_config,reorder_config.reordering_line_ids)
                reorder_config.update_next_run_date(reorder_config)
