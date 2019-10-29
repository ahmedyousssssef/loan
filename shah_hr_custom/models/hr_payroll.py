# -*- coding: utf-8 -*-
from __future__ import division
from datetime import datetime, timedelta
from openerp import api, fields, models, _
from openerp.exceptions import UserError, Warning
from openerp import SUPERUSER_ID
import pytz


class HrPayrollRule(models.Model):
    _name = 'hr.payslip.rule'
    _rec_name = 'name'

    name = fields.Char('Description')
    code = fields.Char('Code')
    num_of_days = fields.Float(string="Number Of Days", required=False, )
    num_of_hours = fields.Float(string="Number Of Hours", required=False, )
    pay_amount = fields.Float(string="Pay Amount", required=False, )
    rule_id = fields.Many2one(comodel_name="hr.payslip", string="Payslip", required=False, )


class hr_payroll(models.Model):
    _inherit = 'hr.payslip'

    attend_rule_ids = fields.One2many(comodel_name="hr.payslip.rule", string="Attendance Rules",
                                      inverse_name='rule_id', )
    deduction_amount = fields.Float(string="Deduction Amount",  required=False,compute='_compute_deduction_amount' )
    overtime_amount = fields.Float(string="OverTime Amount",  required=False,compute='_compute_overtime_amount' )
    absent_amount = fields.Float(string="Absence Amount",  required=False,compute='_compute_absent_amount')

    @api.multi
    def get_attendance_lines(self):
        for record in self:
            record.attend_rule_ids.unlink()
            val_late = 0.0
            val_early = 0.0
            val_absence = 0.0
            overtime_hour = 0.0
            overtime_amount = 0.0
            val_deduction = 0.0
            rules = []
            user_id = self.env['res.users']
            attendance_obj = self.env['hr.attendance']
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            user = user_id.browse(SUPERUSER_ID)
            tz = pytz.timezone(user.partner_id.tz) or pytz.utc

            def daterange(start_date, end_date):
                for n in range(int((end_date - start_date).days) + 1):
                    yield start_date + timedelta(n)

            def get_time_from_float(float_time):
                str_time = str(float_time)
                str_hour = str_time.split('.')[0]
                str_minute = ("%2d" % int(str(float("0." + str_time.split('.')[1]) * 60).split('.')[0])).replace(' ', '0')
                minute = (float(str_hour) * 60) + float(str_minute)
                return minute

            if not record.employee_id.attendance_id:
                raise Warning(_("You Should Choose Attendance Rules on Employee"))

            permission = record.employee_id.attendance_id.permission or 0.0
            search_domain = [
                ('check_in', '>=', record.date_from),
                ('check_out', '<=', record.date_to),
                ('employee_id', '=', record.employee_id.id),
            ]
            hours = record.employee_id.calendar_id.work_period
            attendance_ids = attendance_obj.search(search_domain)
            start_date = datetime.strptime(str(record.date_from), "%Y-%m-%d")
            end_date = datetime.strptime(str(record.date_to), "%Y-%m-%d")
            weekend_days = [day.dayofweek for day in record.employee_id.calendar_id.weekend_ids]
            attendances = [x.check_in[0:10] for x in attendance_ids]
            for single_date in daterange(start_date, end_date):
                if str(single_date.date()) in attendances:
                    for attendance in attendance_ids:
                        attendance_datetime = pytz.utc.localize(
                            datetime.strptime(attendance.check_in, DATETIME_FORMAT)).astimezone(tz)
                        if attendance_datetime.date() == single_date.date():
                            late = 0.0
                            early = 0.0
                            if attendance.late > 0.0:
                                late = get_time_from_float(attendance.late)
                                if permission > 0.0:
                                    if permission >= late:
                                        permission -= late
                                        late = 0.0
                                    else:
                                        late -= permission
                                        permission = 0.0
                                else:
                                    if record.employee_id.attendance_id.rule_deduction_ids:
                                        for rule in record.employee_id.attendance_id.rule_deduction_ids.filtered(
                                                lambda r: r.type == 'late'):
                                            if rule.code not in rules:
                                                time_from = get_time_from_float(rule.time_from)
                                                time_to = get_time_from_float(rule.time_to)
                                                if late >= time_from and late <= time_to:
                                                    late = 0.0
                                                    rules.append(rule.code)
                                                    if rule.warning:
                                                        continue
                                                    elif rule.absent:
                                                        val_absence += 1
                                                    else:
                                                        val_deduction += rule.deduction
                            if attendance.early > 0.0:
                                early = get_time_from_float(attendance.early)
                                if permission > 0.0:
                                    if permission >= early:
                                        permission -= early
                                        early = 0.0
                                    else:
                                        early -= permission
                                        permission = 0.0
                            val_late += late
                            val_early += early
                            overtime_hour += attendance.over_time_hour
                            overtime_amount += attendance.over_time_amount
                else:
                    if single_date.strftime('%A') not in weekend_days:
                        val_absence += 1

            rrule = [
                {
                    'name': 'Late Check In',
                    'sequence': 10,
                    'code': 'Late',
                    'num_of_days': val_late / 60 / hours,
                    'num_of_hours': val_late / 60,
                    'pay_amount': 0.0,
                    'rule_id': record.id,
                },
                {
                    'name': 'Early Check Out',
                    'code': 'Early',
                    'num_of_days':val_early / 60 / hours,
                    'num_of_hours': val_early / 60,
                    'pay_amount': 0.0,
                    'rule_id': record.id,
                },
                {
                    'name': 'Overtime',
                    'code': 'Overtime',
                    'num_of_days': overtime_hour / hours,
                    'num_of_hours': overtime_hour,
                    'pay_amount': overtime_amount or 0.0,
                    'rule_id': record.id,
                },

                {
                    'name': 'Deduction',
                    'code': 'Deduction',
                    'num_of_days': val_deduction,
                    'num_of_hours': val_deduction * hours,
                    'pay_amount': 0.0,
                    'rule_id': record.id,
                },
                {
                    'name': 'Absence',
                    'code': 'Absence',
                    'num_of_days': val_absence,
                    'num_of_hours': val_absence * hours,
                    'pay_amount': 0.0,
                    'rule_id': record.id,
                }
            ]

            for rr in rrule:
                record.write({'attend_rule_ids':[(0,0,rr)]})

    # @api.multi
    # def compute_sheet(self):
    #     self.get_attendance_lines()
    #     res = super(hr_payroll,self).compute_sheet()
    #     return res


    @api.one
    @api.depends('attend_rule_ids')
    def _compute_deduction_amount(self):
        for record in self:
            amount = 0.0
            if record.attend_rule_ids:
                for line in record.attend_rule_ids.filtered(lambda r :r.code in ['Late','Early','Deduction']):
                    amount += line.pay_amount
            record.deduction_amount = amount

    @api.one
    @api.depends('attend_rule_ids')
    def _compute_overtime_amount(self):
        for record in self:
            if record.attend_rule_ids:
                for line in record.attend_rule_ids.filtered(lambda r :r.code == 'Overtime'):
                   record.overtime_amount = line.pay_amount

    @api.one
    @api.depends('attend_rule_ids')
    def _compute_absent_amount(self):
        for record in self:
            if record.attend_rule_ids:
                for line in record.attend_rule_ids.filtered(lambda r :r.code == 'Absence'):
                   record.absent_amount = line.pay_amount




