# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from openerp.exceptions import UserError, Warning


#________________________________________________ Model

class hr_attendance_bonus(models.Model):
    _name = 'hr.attendance.bonus'
    _rec_name = 'name'

    name = fields.Char(string='Name',compute='_compute_name', store=True, readonly=True, )
    bonus_type = fields.Selection(string='Bonus Type', selection=[('hour', 'Hour Bonus'), ('fixed', 'Fixed Bonus')],
                                  default='hour', readonly=False, )
    time_from = fields.Float(string='From')
    time_to = fields.Float(string='To')
    start = fields.Float(string='Start')
    bonus_hours = fields.Float(string='Bonus (Hours)')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id.id, )
    bonus_fixed = fields.Monetary(string='Bonus', currency_field='currency_id', )
    rest_day = fields.Boolean(string='Rest Day')



    @api.one
    @api.depends('bonus_type','time_from','time_to','bonus_hours','bonus_fixed','rest_day')
    def _compute_name(self):
        if self.bonus_type:
            type = dict(self.fields_get(allfields=['bonus_type'])['bonus_type']['selection'])[self.bonus_type]
            if self.bonus_type == 'hour':

                if self.rest_day:
                    self.name = type + '[' + str(self.bonus_hours) + 'Hours] Rest Day'
                else:
                    self.name = type + '[' + str(self.bonus_hours) + 'Hours]'
            else:
                self.name = type + '[' + str(self.bonus_fixed) + self.currency_id.symbol + ']'
        pass
