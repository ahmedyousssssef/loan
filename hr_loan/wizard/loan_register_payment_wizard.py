# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from datetime import datetime, timedelta, date

LOGGER = logging.getLogger(__name__)


class LoanRegisterPaymentWizard(models.TransientModel):
    _name = 'loan.register.payment.wizard'

    def _get_default_amount(self):
        loan_id = self.env.context.get('active_id')
        loan = self.env['hr.loan'].browse(loan_id)

        amount = loan.requested_amount
        return amount

    def _get_default_loan_journal(self):
        journal_obj = self.env['account.journal'].search([('is_loan_journal', '=', True)], limit=1)
        journal = journal_obj.id
        return journal

    def _get_default_partner(self):
        loan_id = self.env.context.get('active_id')
        loan = self.env['hr.loan'].browse(loan_id)
        partner = loan.employee_id.address_home_id.id
        return partner

    loan_journal_id = fields.Many2one(comodel_name='account.journal', string='Loan Journal',
                                      default=lambda self: self._get_default_loan_journal())
    bank_journal_id = fields.Many2one(comodel_name='account.journal', string='Bank Journal')
    amount = fields.Float(string='Amount', default=lambda self: self._get_default_amount())
    rel_partner_id = fields.Many2one(comodel_name='res.partner', string='Related Partner',
                                     default=lambda self: self._get_default_partner())

    date = fields.Date(string='Date', default=datetime.today())

    def create_debit_item(self, move):
        loan_id = self.env.context.get('active_id')
        loan = self.env['hr.loan'].browse(loan_id)

        date = datetime.strptime(move.date, '%Y-%m-%d').date()
        if self.loan_journal_id.default_debit_account_id:
            account = self.loan_journal_id.default_debit_account_id.id
            name = 'Recieve ' + loan.employee_id.name
            query = "insert into account_move_line (account_id,partner_id,debit,name,move_id,date_maturity) values ({},{},{},'{}',{},TO_DATE('{}','%Y-%m-%d'))".format(
                account, self.rel_partner_id.id, self.amount, name, move.id, move.date)
            self.env.cr.execute(query)
        else:
            raise ValidationError("Please Check The Default Debit Account")

    def create_credit_item(self, move):
        loan_id = self.env.context.get('active_id')
        loan = self.env['hr.loan'].browse(loan_id)
        date = datetime.strptime(move.date, '%Y-%m-%d').date()
        if self.bank_journal_id.default_credit_account_id:
            account = self.bank_journal_id.default_credit_account_id.id
            name = 'Send ' + loan.employee_id.name
            query = "insert into account_move_line (account_id,credit,name,move_id,date_maturity) values ({},{},'{}',{},TO_DATE('{}','%Y-%m-%d'))".format(
                account, self.amount, name, move.id, move.date)
            self.env.cr.execute(query)
        else:
            raise ValidationError("Please Check The Default Credit Account")

    def validate_payment(self):
        loan_id = self.env.context.get('active_id')
        loan = self.env['hr.loan'].browse(loan_id)
        loan_name = loan.name

        vals = {
            'date': self.date,
            'ref': loan_name,
            'journal_id': self.loan_journal_id.id,
            # 'partner_id': self.rel_partner_id.id,
            'state': 'draft'
        }

        journal_entry = self.env['account.move'].create(vals)
        self.create_debit_item(journal_entry)
        self.create_credit_item(journal_entry)
        loan.journal_created = True
        journal_entry.post()
        return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'loan.register.payment.view.wizard',
            'target': 'new',
            'context': {'default_name': "Successfully Submitted."}
        }


class LoanRegisterPaymentViewWizard(models.TransientModel):
    _name = 'loan.register.payment.view.wizard'
