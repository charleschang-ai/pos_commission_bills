# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import json
from odoo.tools.json import json_default
from odoo.tools.safe_eval import pytz


class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard'

    def generate_report_by_execl(self):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        start_date = self.start_date.astimezone(user_tz).replace(tzinfo=None)
        end_date = self.end_date.astimezone(user_tz).replace(tzinfo=None)

        data = {
            'date_start': start_date.strftime('%Y-%m-%d %H:%M:%S'),
            'date_stop': end_date.strftime('%Y-%m-%d %H:%M:%S'),
            'date1': self.start_date.strftime('%Y-%m-%d %H:%M:%S'),
            'date2': self.end_date.strftime('%Y-%m-%d %H:%M:%S'),
            'config_ids': self.pos_config_ids.ids
        }
        return {
            'type': 'ir.actions.act_url',
            'url': '/pos/excel/export?data=%s' % json.dumps(data),
            'target': 'self',
        }
