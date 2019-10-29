# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

LOGGER = logging.getLogger(__name__)

class LoanPaymentWizard(models.TransientModel):
    _name = 'loan.payment.wizard'


    def _get_default_payment(self):
        loan_id = self.env.context.get('active_id')
        loan = self.env['hr.loan'].browse(loan_id)
        amount = 0
        for line in loan.loan_line:
            if line.state in ('unpaid','partial_paid'):
                amount += line.amount - line.paid_amount
        return amount



    remainning_amount = fields.Float(string="Remaining",default=lambda self: self._get_default_payment(),  required=False, )
    pay_amount = fields.Float(string="Pay Amount",  required=True, )

    pay_from = fields.Selection(string="Pay From", selection=[('start', 'Next Installment'), ('end', 'End Installment to Earlier'), ], required=True,default='start' )

    def confirm_payment(self):
        if self.remainning_amount < self.pay_amount:
            raise ValidationError('Paid Amount is greater than unpaid of the loan')
        reamin_amount = self.pay_amount
        loan_id = self.env.context.get('active_id')
        loan = self.env['hr.loan'].browse(loan_id)
        loan_lines = self.env['hr.loan.line']
        if self.pay_from == 'start':
            loan_lines = self.env['hr.loan.line'].search([
                ('loan_id','=',loan_id),
                ('state','in',('unpaid','partial_paid'))
                                          ],order='date asc')

        elif self.pay_from == 'end':
            loan_lines = self.env['hr.loan.line'].search([
                ('loan_id','=',loan_id),
                ('state','in',('unpaid','partial_paid'))
                                          ],order='date Desc')

        lines_count = len(loan_lines)
        i = 0

        if lines_count >= 1:
            while(reamin_amount > 0 and i < lines_count):
                line_pay = min((loan_lines[i].amount - loan_lines[i].paid_amount),reamin_amount)
                loan_lines[i].paid_amount += line_pay
                if loan_lines[i].paid_amount == loan_lines[i].amount:
                    loan_lines[i].write({'state' : 'paid'})
                elif loan_lines[i].paid_amount > 0 and loan_lines[i].paid_amount < loan_lines[i].amount:
                    loan_lines[i].write({'state' : 'partial_paid'})

                reamin_amount -= line_pay
                i += 1

            all_loans_lines = self.env['hr.loan.line'].search([('loan_id', '=', loan.id)])
            open = False
            for line_loan in all_loans_lines:
                if line_loan.state != 'paid':
                    open = True

            if not open:
                loan.write({'state': 'closed'})






