# -*- coding: utf-8 -*-
from openerp import fields, models, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # @api.one
    # @api.depends('wage', 'number_of_salary_multipliers', 'variable_salary', 'allowances')
    # def compute_total_loan_budget(self):
    #     total_loan_budget = 0
    #     if self.wage and self.number_of_salary_multipliers:
    #         total_loan_budget = (self.wage + self.variable_salary + self.allowances) * self.number_of_salary_multipliers
    #     self.total_loan_budget = total_loan_budget
    #     return True

    # number_of_salary_multipliers = fields.Float(string="Number Of Salary Multipliers", default=1.2, required=False, )
    # total_loan_budget = fields.Float(string="Total Loan Budget", compute=compute_total_loan_budget, store=True,
    #                                  required=False, )
