# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import datetime


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def Get_Loan_Rule(self, payslip):
        loan_amount = 0
        if payslip.loan_lines_ids:
            loan_amount = sum(
                (one_loan_line.amount - one_loan_line.paid_amount) for one_loan_line in payslip.loan_lines_ids)
        return loan_amount

    @api.one
    def _compute_total_loan_unpaid(self):
        total_unpaid_loan = 0
        loan_line_obj = self.env['hr.loan.line']
        if self.id:
            loan_line_data = loan_line_obj.search(
                [('loan_id.employee_id', '=', self.id), ('state', 'in', ('unpaid', 'partial_paid'))])
            for loan_line in loan_line_data:
                total_unpaid_loan += loan_line.amount - loan_line.paid_amount

        self.total_unpaid_loan = total_unpaid_loan
        return True

    total_unpaid_loan = fields.Float(string="Total Loan Unpaid", compute=_compute_total_loan_unpaid, required=False, )
