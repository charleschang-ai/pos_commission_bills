from odoo import models, fields, api


class CommissionWizard(models.TransientModel):
    _name = 'commission.wizard'
    _description = 'Commission Calculation Wizard'

    @api.model
    def _default_get_full_refund(self):
        if self.env.context.get('active_ids', []):
            active_ids = self.env.context.get('active_ids', [])
            pos_lines = self.env['pos.order.line'].browse(active_ids)
            for line in pos_lines:
                if line.refunded_qty == line.qty:
                    return True
            return False
        return False

    partner_id = fields.Many2one('res.partner', string="Contact", required=True)
    date_start = fields.Date(string="Date Start", default=fields.Date.today)
    is_full_refund = fields.Boolean("Full Refund", default=_default_get_full_refund)

    def action_calculate_commission(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        pos_lines = self.env['pos.order.line'].browse(active_ids)

        bill_lines = []
        for line in pos_lines:
            if line.refund_orderline_ids:

                storage_fees = (line.qty - line.refunded_qty) * line.storage_fees
                price_subtotal_incl = (line.qty - line.refunded_qty) * line.price_unit * (1 - line.discount)
                profit = price_subtotal_incl - line.commission_fees - storage_fees
            else:
                storage_fees = line.qty * line.storage_fees
                profit = line.price_subtotal_incl - line.commission_fees - storage_fees
            bill_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.customer_note,
                'quantity': 1,
                'original_qty': line.qty,
                'original_price_unit': line.price_unit,
                'original_price': line.price_subtotal_incl,
                'commission_rate': line.commission_rate,
                'commission_fees': line.commission_fees,
                'storage_fees': storage_fees,
                'price_unit': profit,
                'pos_line_id': line.id
            }))

        form_view = self.env.ref('account.view_move_form')

        return {
            'name': 'Commission Bill Preview',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'views': [[form_view.id, 'form']],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_move_type': 'in_invoice',
                'default_invoice_date': self.date_start or fields.Date.today(),
                'default_invoice_line_ids': bill_lines,
            },
        }



