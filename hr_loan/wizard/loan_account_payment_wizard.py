# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
import logging
from datetime import datetime, timedelta, date

LOGGER = logging.getLogger(__name__)


class LoanAccountPaymentWizard(models.TransientModel):
    _name = 'loan.account.payment.wizard'

    payment_journal_id = fields.Many2one(comodel_name='account.journal', string='Payment Journal',
                                         domain='[("type","in",["bank","cash"])]')

    @api.multi
    def generate_payment(self):
        loan_id = self.env.context.get('active_id')
        loan = self.env['loan.payment'].browse(loan_id)
        acc_payment_date = 'Loan/' + datetime.now().strftime("%Y") + '/' + loan.name
        vals = {
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'partner_id': loan.partner_id.id,
            'amount': loan.req_amount,
            'journal_id': self.payment_journal_id.id,
            'communication': loan.desc,
            'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
            'source_doc': acc_payment_date
        }
        loan.state = 'closed'
        self.env['account.payment'].create(vals)
        self.env['account.payment']._onchange_journal()
