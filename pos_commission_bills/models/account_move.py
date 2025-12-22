# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    original_qty = fields.Float(string='Qty', default=0)
    original_price_unit = fields.Float(string='Original Unit Price', default=0)
    commission_rate = fields.Float(string='Commission Rate', default=0)
    storage_fees = fields.Monetary(string='Storage Fees', default=0, currency_field='currency_id')
    original_price = fields.Monetary(string='Original price', default=0, currency_field='currency_id')
    pos_line_id = fields.Many2one('pos.order.line', string="POS Line")
    commission_fees = fields.Monetary(string='Commission Fees', currency_field='currency_id', default=0)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()
        pos_lines = self.line_ids.filtered(lambda l: l.pos_line_id)
        pos_lines.mapped('pos_line_id').write({'is_billed': True, 'billed_date': fields.Datetime.now()})
        for line in pos_lines:
            line.pos_line_id.total_storage_fees = line.storage_fees
            line.pos_line_id.vendor_id = self.partner_id.id
        return res

    def action_cancel(self):
        res = super().action_cancel()
        pos_lines = self.invoice_line_ids.filtered(lambda l: l.pos_line_id)
        pos_lines.mapped('pos_line_id').write({'is_billed': False, 'billed_date': False})
        for line in pos_lines:
            line.pos_line_id.total_storage_fees = 0
            line.pos_line_id.vendor_id = False
        return res

    def button_draft(self):
        res = super().button_draft()
        pos_lines = self.invoice_line_ids.filtered(lambda l: l.pos_line_id)
        pos_lines.mapped('pos_line_id').write({'is_billed': False, 'billed_date': False})
        for line in pos_lines:
            line.pos_line_id.total_storage_fees = 0
            line.pos_line_id.vendor_id = False
        return res
