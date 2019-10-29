# -*- coding: utf-8 -*-
from openerp import fields, models, api, _


class LoanPayment(models.Model):
    _name = 'loan.payment'

    name = fields.Char()
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    partner_type = fields.Selection(
        [('customer', 'Customer'),
         ('vendor', 'Vendor'),
         ('none', 'None'),
         ('both', 'Customer and Vendor')], string='Partner Type')
    req_amount = fields.Float(string='Requested Amount')
    desc = fields.Char(string='Loan')
    req_date = fields.Date(string='Date Of Request')
    loan_line_ids = fields.One2many('acc.loan.line', 'loan_id', 'Loan Lines')
    state = fields.Selection(
        [('open', 'Open'),
         ('closed', 'Done'),
         ], default='open', string='State')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('loan.payment')
        return super(LoanPayment, self).create(vals)


class AccLoanLine(models.Model):
    _name = 'acc.loan.line'

    date = fields.Date()
    amount = fields.Float(string='')
    loan_id = fields.Many2one('loan.payment', string='Loan Reference', readonly=True)
