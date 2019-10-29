# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import datetime


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def action_payslip_done(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')
        obj = super(HrPayslip, self).action_payslip_done()
        for slip in self:
            if slip and slip.loan_lines_ids:

                total_loans = []
                loan_id = False
                for line in slip.loan_lines_ids:
                    line.write({'state': 'paid'})
                    line.update({'paid_amount': line.amount})
                    if line.loan_id not in total_loans:
                        total_loans.append(line.loan_id)

                if total_loans:
                    for loan_id in total_loans:
                        all_loans_lines = self.env['hr.loan.line'].search(
                            [('loan_id', '=', loan_id.id), ('loan_id.state', '=', 'approved')])
                        open = False
                        for line_loan in all_loans_lines:
                            if line_loan.state != 'paid':
                                open = True

                        if not open:
                            loan_id.write({'state': 'closed'})

        return obj

    def Get_Loan_Rule(self, payslip):
        loan_amount = 0
        if payslip.loan_lines_ids:
            loan_amount = sum(
                (one_loan_line.amount - one_loan_line.paid_amount) for one_loan_line in payslip.loan_lines_ids)
        return loan_amount

    @api.one
    @api.depends('employee_id', 'date_from', 'date_to')
    def _get_loan_lines(self):
        line_ids = []
        if self.employee_id and self.date_from and self.date_to:
            loans_lines = self.env['hr.loan.line'].search(
                [('loan_id.employee_id', '=', self.employee_id.id), ('loan_id.state', 'in', ['sent','approved']),
                 ('state', 'in', ('unpaid', 'partial_paid')),
                 ('date', '>=', self.date_from),
                 ('date', '<=', self.date_to)])
            for line in loans_lines:
                line_ids.append(line.id)
                # line.write({'payslip_id': self.id})

            self.loan_lines_ids = line_ids
            return

        return True

    @api.multi
    def compute_sheet(self):
        self._get_loan_lines()

        res = super(HrPayslip, self).compute_sheet()
        return res

    loan_lines_ids = fields.One2many(comodel_name="hr.loan.line", inverse_name="payslip_id", compute=_get_loan_lines,
                                     store=True, string="Loan Lines", required=False, )

    # loans = fields.Float(compute='_compute_loans')
    #
    # def _compute_loans(self):
    #     for payslip in self:
    #         loan_obj = payslip.env['hr.loan'].search(
    #             [('employee_id', '=', payslip.employee_id.id), ('state', '=', 'approved')])
    #         loans_lines = payslip.env['hr.loan.line'].search([('loan_id', 'in', [loan_obj.id]),
    #                                                  ('state', '=', 'unpaid'),
    #                                                  ('date', '>=', payslip.date_from),
    #                                                  ('date', '<=', payslip.date_to)])
    #
    #         payslip.loans = sum(loan.amount for loan in loans_lines)

    # @api.multi
    # def compute_sheet(self):
    #     for payslip in self:
    #         number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
    #         # delete old payslip lines
    #         payslip.line_ids.unlink()
    #         # set the list of contract for which the rules have to be applied
    #         # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
    #         contract_ids = payslip.contract_id.ids or \
    #                        self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
    #         lines = [(0, 0, line) for line in self.get_payslip_lines(contract_ids, payslip.id)]
    #
    #         ## close the loan for this employee,cuz every sattements was paid
    #         loan_obj = payslip.env['hr.loan'].search(
    #             [('employee_id', '=', payslip.employee_id.id), ('state', '=', 'approved')])
    #         loans_lines = payslip.env['hr.loan.line'].search([('loan_id', 'in', [loan_obj.id]),
    #                                                           ('state', '=', 'unpaid'),
    #                                                           ('date', '>=', payslip.date_from),
    #                                                           ('date', '<=', payslip.date_to)])
    #
    #         # for l in loans_lines: l.write({'state': 'paid'})
    #         if not payslip.env['hr.loan.line'].search([('loan_id', 'in', [loan_obj.id]),
    #                                                    ('state', '=', 'unpaid')]):
    #             for loan in loan_obj:
    #                 loan.write({'state': 'closed'})
    #
    #     payslip.write({'line_ids': lines, 'number': number})
    #     return True
