# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
# from odoo.excpetions import ValidationError


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    commission_rate = fields.Float(string='Commission Rate', default=0)
    storage_fees = fields.Monetary(string='Storage Fees', default=2, currency_field='currency_id')
    is_commission = fields.Boolean(string='Is Commission', default=False, compute="_compute_is_commission", store=True)
    bill_line_ids = fields.One2many(
        'account.move.line', 'pos_line_id', string='Bill Lines'
    )
    is_billed = fields.Boolean(string='Is Billed', default=False)
    status_display = fields.Char(string="Billing Status", compute='_compute_status_display', store=True)
    order_date = fields.Datetime(string="Order Date", related="order_id.date_order")

    commission_fees = fields.Monetary(
        string='Commission Fees',
        compute='_compute_commission_fees',
        inverse='_inverse_commission_fees',
        store=True,
        currency_field='currency_id'
    )
    commission_fees_base = fields.Monetary(
        string='Commission Fees Base',
        compute='_compute_commission_fees',
        store=True,
        currency_field='currency_id'
    )

    # service fee can modify by backend, default that 0
    service_fee = fields.Monetary(
        string='Service Fee',
        default=0,
        currency_field='currency_id',
        store=True
    )

    spin_off_fee = fields.Monetary(
        string='3rd Partner',
        default=0,
        currency_field='currency_id'
    )

    is_locked = fields.Boolean(string='Locked', default=False)
    billed_date = fields.Datetime(string='Billed Date')
    total_storage_fees = fields.Monetary(string='Total Storage Fees', default=0, currency_field='currency_id')
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    customer_id = fields.Many2one('res.partner', related="product_id.customer_id", string="Customer")

    remaining_qty = fields.Integer("Remaining Qty", default=0, compute="_compute_remaining_qty", store=True)

    @api.depends('refunded_qty', 'price_subtotal_incl', 'qty')
    def _compute_remaining_qty(self):
        for line in self:
            line.remaining_qty = line.qty - line.refunded_qty

    @api.depends('commission_rate', 'price_subtotal_incl', 'refunded_qty')
    def _compute_commission_fees(self):
        for line in self:
            if line.refunded_orderline_id or not line.is_commission:
                line.commission_fees = 0
            elif line.refund_orderline_ids:
                remaining_qty = line.qty - line.refunded_qty
                if remaining_qty == 0:
                    line.commission_fees = 0
                else:
                    price_subtotal_incl = remaining_qty * line.price_unit * (1 - line.discount)
                    commission_fees_base = price_subtotal_incl * (line.commission_rate / 100)
                    line.commission_fees_base = commission_fees_base
                    if commission_fees_base < 10:
                        commission_fees_base = 10
                    line.commission_fees = commission_fees_base
            else:
                commission_fees_base = line.price_subtotal_incl * (line.commission_rate / 100)
                line.commission_fees_base = commission_fees_base
                if commission_fees_base < 10:
                    commission_fees_base = 10
                line.commission_fees = commission_fees_base

    def _inverse_commission_fees(self):
        for line in self:
            base = line.price_subtotal_incl or 0.0
            line.commission_rate = (line.commission_fees / base) * 100.0 if base else 0.0


    @api.depends('is_billed')
    def _compute_status_display(self):
        for line in self:
            if line.is_billed:
                line.status_display = "Billed"
            else:
                line.status_display = "Unbilled"

    @api.onchange('product_id')
    def on_change_product_commission_and_storage(self):
        for line in self:
            if line.product_id:
                line.commission_rate = line.product_id.commission_rat or 0.0
                line.commission_fees = line.product_id.storage_fees or 0.0
            else :
                line.commission_rate = 0.0
                line.storage_fees = 0.0

    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        params += ['commission_rate', 'storage_fees']
        return params

    def _export_for_ui(self, orderline):
        """Export the POS order line data for the UI."""
        return {
            'commission_rate': orderline.commission_rate,
            'storage_fees': orderline.storage_fees,
            **super()._export_for_ui(orderline),
        }

    @api.depends('product_id')
    def _compute_is_commission(self):
        for record in self:
            record.is_commission = bool(record.product_id and record.product_id.commission_ok)

    def update_commission_readonly_state(self, readonly=True):
        view = self.env.ref('asta_pos_commission_customization.view_pos_order_line_tree')
        if not view:
            return
        root = etree.fromstring(view.arch)

        for f_name in ('commission_rate', 'commission_fees', 'storage_fees'):
            for node in root.xpath(f"//field[@name='{f_name}']"):
                if readonly:
                    node.set('readonly', '1')
                else:
                    node.attrib.pop('readonly', None)

        view.arch = etree.tostring(root, encoding='unicode')

        self.write({'is_locked': readonly})

    def action_lock_commission_view(self):
        self.update_commission_readonly_state(readonly=True)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_unlock_commission_view(self):
        self.update_commission_readonly_state(readonly=False)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

