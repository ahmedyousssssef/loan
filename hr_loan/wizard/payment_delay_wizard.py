# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

LOGGER = logging.getLogger(__name__)

class PaymentDelayWizard(models.TransientModel):
    _name = 'payment.delay.wizard'

    num_months = fields.Integer(string="Number of Months To Delay", default=1, )

    def action_apply(self):
        active_id = self._context.get('active_id')
        loan = self.env['hr.loan'].browse(active_id)
        if self.num_months:
            for line in loan.loan_line:
                if line.state != 'paid':
                    line.write({'date':str(fields.Datetime.from_string(line.date) + relativedelta(months=self.num_months))})