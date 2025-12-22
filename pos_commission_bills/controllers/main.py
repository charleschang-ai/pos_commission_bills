# -*- coding: utf-8 -*-
#################################################################################
# Author      : Charles.
# Copyright(c): Charles
# All Rights Reserved.
# You should have received a copy of the License along with this program.
#################################################################################
import logging
from datetime import datetime, timedelta

import pytz

from odoo.osv.expression import AND

_logger = logging.getLogger(__name__)
import re
from odoo.http import request
from odoo import _, fields
import json

from odoo import http
from odoo.http import content_disposition
import io
import xlsxwriter


class XLSXReportController(http.Controller):
    @http.route(['/pos/excel/export'], type='http', auth='user', csrf=False)
    def export_excel(self, data=None, **kwargs):
        params = json.loads(data or '{}')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        report_data = self._prepare_report_data(params)
        self._write_excel_report(workbook, report_data)

        workbook.close()
        output.seek(0)
        filename = 'pos_report_%s.xlsx' % datetime.now().strftime('%Y%m%d_%H%M%S')
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(filename))
        ]
        return request.make_response(output.getvalue(), headers)

    def _prepare_report_data(self, params):
        config_ids = params.get('config_ids', [])
        date_start = params.get('date_start', fields.date.today())
        date_stop = params.get('date_stop', fields.date.today())

        date1 = params.get('date1', fields.date.today())
        date2 = params.get('date2', fields.date.today())

        date_start2, date_stop2 = self._get_date_start_and_date_stop(
            date_start, date_stop,
        )

        domain = [
            ('state', 'in', ['paid', 'invoiced', 'done']),
            ('date_order', '>=', date1),
            ('date_order', '<=', date2),
        ]
        if config_ids:
            domain = AND([domain, [('config_id', 'in', config_ids)]])
        orders = request.env['pos.order'].sudo().search(domain)

        payments = request.env['pos.payment'].sudo().search([
            ('pos_order_id', 'in', orders.ids)
        ])

        storage_lines = request.env['pos.order.line'].sudo().search([
            ('order_id.state', 'in', ['paid', 'invoiced', 'done']),
            ('is_commission', '=', True),
            ('is_billed', '=', True),
            ('billed_date', '>=', date1),
            ('billed_date', '<=', date2),
            # ('refund_orderline_ids', '=', False),
            ('refunded_orderline_id', '=', False),
        ])
        storage_fees = sum(line.total_storage_fees or 0.0 for line in storage_lines)

        # 3.2 Total Amount = sum(order.amount_paid) + storage_fees
        total_paid = sum(o.amount_paid for o in orders)
        total_amount = total_paid + storage_fees

        # 3.3 Commission & Profit (including service fee)
        commission_lines = request.env['pos.order.line'].sudo().search([
            ('order_id', 'in', orders.ids),
            ('is_commission', '=', True),
            # ('refund_orderline_ids', '=', False),
            ('refunded_orderline_id', '=', False),
        ])
        commission = sum(line.commission_fees or 0.0 for line in commission_lines)

        # service fee part
        # search the service fee
        service_lines = request.env['pos.order.line'].sudo().search([
            ('order_id.state', 'in', ['paid', 'invoiced', 'done']),
            ('service_fee', '>', 0),
            ('order_id.date_order', '>=', date1),
            ('order_id.date_order', '<=', date2),
            # ('refund_orderline_ids', '=', False),
            ('refunded_orderline_id', '=', False),
        ])
        service_fee = sum(line.service_fee or 0.0 for line in service_lines)

        spin_off_lines = request.env['pos.order.line'].sudo().search([
            ('order_id.state', 'in', ['paid', 'invoiced', 'done']),
            ('spin_off_fee', '>', 0),
            ('order_id.date_order', '>=', date1),
            ('order_id.date_order', '<=', date2),
            # ('refund_orderline_ids', '=', False),
            ('refunded_orderline_id', '=', False),
        ])
        spin_off = sum(line.spin_off_fee or 0.0 for line in spin_off_lines)

        cost_lines = request.env['pos.order.line'].sudo().search([
            ('order_id.state', 'in', ['paid', 'invoiced', 'done']),
            ('is_commission', '=', False),
            ('product_id.standard_price', '>', 0),
            ('order_date', '>=', date1),
            ('order_date', '<=', date2),
            # ('refund_orderline_ids', '=', False),
            ('refunded_orderline_id', '=', False),
        ])
        # cost_fee = sum(line.standard_price or 0.0 for line in cost_lines)
        cost_fee = sum(
            (line.price_subtotal_incl or 0.0) - (line.product_id.standard_price * (line.qty - line.refunded_qty) or 0.0)
            for line in cost_lines)

        # profit = commission + service_fee + storage_fees - spin_off
        profit = commission + service_fee + storage_fees - spin_off + cost_fee

        commission = commission - spin_off

        # 3Cash / Electronic / Bank Charges / Cash Out
        cash_payments = payments.filtered(
            lambda
                p: p.payment_method_id and p.payment_method_id.journal_id and p.payment_method_id.journal_id.type == 'cash'
        )

        electronic_payments = payments.filtered(
            lambda
                p: p.payment_method_id and p.payment_method_id.journal_id and p.payment_method_id.journal_id.type != 'cash'
        )

        # bank_charge_payments = payments.filtered(
        #     lambda p: p.payment_provider_charges
        # )

        sessions = (
            request.env['pos.session']
            .sudo()
            .search([
                ('config_id', 'in', config_ids),
                ('start_at', '<=', date2),
                ('state', '!=', 'cancel'),
            ])
        )

        session_ids = sessions.ids or [0]

        stmt_domain = [
            ('pos_session_id', 'in', session_ids),
            ('create_date', '>=', date1),
            ('create_date', '<=', date2),
            ('amount', '<', 0),
        ]
        statement_lines = request.env['account.bank.statement.line'].sudo().search(stmt_domain)

        cash_out_total = sum(abs(line.amount) for line in statement_lines)

        cash_income = sum(p.amount for p in cash_payments)
        electronic = sum(p.amount for p in electronic_payments)
        # bank_charge = sum(p.payment_provider_charges for p in bank_charge_payments)
        # cash_out = sum(p.amount for p in cash_out_payments)

        # 3.5 for breakdown table
        payment_summary = {}
        for p in payments:
            name = p.payment_method_id.display_name
            payment_summary.setdefault(name, 0.0)
            payment_summary[name] += p.amount

        return {
            'date_start': date_start,
            'date_stop': date_stop,
            'total_amount': total_amount,
            'storage_fees': storage_fees,
            'commission': commission,
            'service_fee': service_fee,
            'profit': profit,
            'cash_income': cash_income,
            'electronic': electronic,
            # 'bank_charge': bank_charge,
            'cash_out': cash_out_total,
            'payment_summary': list(payment_summary.items()),
            'spin_off': spin_off
        }

    def _write_excel_report(self, workbook, data):
        sheet = workbook.add_worksheet('POS Summary')
        # Formats
        header_fmt = workbook.add_format({
            'align': 'center',
            'bold': True,
            'font_size': 12,
            'bg_color': '#F9F9F9',
            'border': 1,
        })
        center_fmt = workbook.add_format({
            'align': 'center',
            'border': 1,
        })
        money_fmt = workbook.add_format({
            'num_format': u'$#,##0.00',
            'align': 'center',
            'border': 1,
        })

        sheet.set_column(0, 12, 18)

        row = 0
        # Title
        sheet.write(row, 0, 'POS Reports', header_fmt)
        sheet.write(row, 2, data['date_start'], header_fmt)
        sheet.write(row, 3, data['date_stop'], header_fmt)

        row += 2

        # ===== Summary =====
        summary_headers = [
            'Total Amount', 'Storage Fees', 'Commission', 'service_fee', 'Profit', '3rd Partner',
            'Cash Income', 'Electronic Income', 'Cash Out'
        ]
        for col, title in enumerate(summary_headers, start=0):
            sheet.write(row, col, title, header_fmt)

        row += 1
        sheet.write(row, 0, data['total_amount'], money_fmt)
        sheet.write(row, 1, data['storage_fees'], money_fmt)
        sheet.write(row, 2, data['commission'], money_fmt)
        sheet.write(row, 3, data['service_fee'], money_fmt)
        sheet.write(row, 4, data['profit'], money_fmt)
        sheet.write(row, 5, data['spin_off'], money_fmt)
        sheet.write(row, 6, data['cash_income'], money_fmt)
        sheet.write(row, 7, data['electronic'], money_fmt)
        # sheet.write(row, 8, data['bank_charge'], money_fmt)
        sheet.write(row, 8, data['cash_out'], money_fmt)

        row += 2

        sheet.write(row, 0, 'Payment Method', header_fmt)
        sheet.write(row, 1, 'Amount', header_fmt)

        row += 1
        for method, amount in data['payment_summary']:
            sheet.write(row, 0, method, center_fmt)
            sheet.write(row, 1, amount, money_fmt)
            row += 1

        # ===== Payment Breakdown Total =====
        total_pay = sum(amount for _, amount in data['payment_summary'])
        sheet.write(row, 0, 'Total', header_fmt)
        sheet.write(row, 1, total_pay, money_fmt)

    def _get_date_start_and_date_stop(self, date_start, date_stop):
        if date_start:
            date_start = fields.Datetime.from_string(date_start)
        else:
            # start by default today 00:00:00
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
            today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
            date_start = today.astimezone(pytz.timezone('UTC')).replace(tzinfo=None)

        if date_stop:
            date_stop = fields.Datetime.from_string(date_stop)
            # avoid a date_stop smaller than date_start
            if (date_stop <= date_start):
                date_stop = date_start + timedelta(days=1, seconds=-1)
        else:
            # stop by default today 23:59:59
            date_stop = date_start + timedelta(days=1, seconds=-1)

        return date_start, date_stop
