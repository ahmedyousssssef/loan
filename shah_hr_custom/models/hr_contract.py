# -*- coding: utf-8 -*-

from openerp import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    fixed_salary = fields.Float(string="Fixed Salary",  required=False, )
    variable_salary = fields.Float(string="Variable Salary",  required=False, )
    additional = fields.Float(string="Additional",  required=False, )