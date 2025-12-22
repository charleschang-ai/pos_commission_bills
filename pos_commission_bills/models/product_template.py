# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    commission_rate = fields.Float(string='Commission Rate', default=0)
    storage_fees = fields.Monetary(string='Storage Fees', default=2, currency_field='currency_id')
    commission_ok = fields.Boolean(string='Commission', default=False)
    customer_id = fields.Many2one(comodel_name="res.partner", string="Customer")
    # deposit_ok = fields.Boolean(string='Deposit', default=False)

    @api.model
    def _load_pos_data_fields(self, config_id):
        results = super()._load_pos_data_fields(config_id)
        results += ['commission_rate', 'storage_fees']
        return results


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _load_pos_data_fields(self, config_id):
        results = super()._load_pos_data_fields(config_id)
        results += ['commission_rate', 'storage_fees']
        return results
