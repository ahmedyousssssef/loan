# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp import api, fields, models, _
from openerp import SUPERUSER_ID
import pytz


# ________________________________________________ Model Inherit

class hr_attendance(models.Model):
    _inherit = 'hr.attendance'

    check_in = fields.Datetime(string="Check In", compute='get_check_in')
    check_out = fields.Datetime(string="Check Out", compute='get_check_out')
    late = fields.Float(string='Late Check In', compute='_compute_late', store=True)
    early = fields.Float(string='Early Check Out', compute='_compute_early', store=True)
    over_time = fields.Float(string='Over Time', compute='_compute_over_time', store=True)
    over_time_amount = fields.Float(string='Over Time Amount', compute='_compute_over_time', store=True)
    over_time_hour = fields.Float(string='Over Time Hour', compute='_compute_over_time', store=True)


    @api.one
    def get_check_in(self):
        if self.action == 'sign_in' and self.name:
            self.check_in = self.name


    @api.one
    def get_check_out(self):
        if self.action == 'sign_out' and self.name:
            self.check_in = self.name


    def get_time_from_float(self,float_time):
        str_time = str(float_time)
        str_hour = str_time.split('.')[0]
        str_minute = ("%2d" % int(str(float("0." + str_time.split('.')[1]) * 60).split('.')[0])).replace(' ', '0')
        minute = (float(str_hour) * 60) + float(str_minute)
        return minute

    def _get_check_time(self, check_date):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        user_id = self.env['res.users']
        user = user_id.browse(SUPERUSER_ID)
        tz = pytz.timezone(user.partner_id.tz) or pytz.utc
        checkdate = pytz.utc.localize(datetime.strptime(check_date, DATETIME_FORMAT)).astimezone(tz)
        return checkdate

    def get_work_from(self, date_in, working_hours_id):
        hour = 0.0
        if type(date_in) is datetime:
            working_hours = working_hours_id
            for line in working_hours.attendance_ids:
                if int(line.dayofweek) == date_in.weekday():
                    hour = line.hour_from
        return hour

    def get_work_to(self, date_out, working_hours_id):
        hour = 0.0
        if type(date_out) is datetime:
            working_hours = working_hours_id
            for line in working_hours.attendance_ids:
                if int(line.dayofweek) == date_out.weekday():
                    hour = line.hour_to
        return hour

    @api.one
    @api.depends('check_in')
    def _compute_late(self):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        if self.check_in and self.employee_id.calendar_id:
            weekend_days = [day.dayofweek for day in self.employee_id.calendar_id.weekend_ids]
            check_in = self._get_check_time(self.check_in).replace(tzinfo=None)
            if check_in.strftime('%A') not in weekend_days:
                wrok_from = self.get_work_from(check_in, self.employee_id.calendar_id)
                str_time = str(wrok_from)
                hour = str_time.split('.')[0]
                minte = str_time.split('.')[1]
                work_start = datetime(year=check_in.year, month=check_in.month, day=check_in.day, hour=00, minute=00) + timedelta(hours=float(hour),minutes=float(minte))
                work_start = pytz.utc.localize(datetime.strptime(str(work_start), DATETIME_FORMAT)).replace(tzinfo=None)
                if check_in > work_start:
                    dif = check_in - work_start
                    self.late=float(dif.seconds)/3600

    @api.one
    @api.depends('check_out')
    def _compute_early(self):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        if self.check_out and self.employee_id.calendar_id:
            weekend_days = [day.dayofweek for day in self.employee_id.calendar_id.weekend_ids]
            check_out = self._get_check_time(self.check_out).replace(tzinfo=None)
            if check_out.strftime('%A') not in weekend_days:
                wrok_to = self.get_work_to(check_out, self.employee_id.calendar_id)
                str_time = str(wrok_to)
                hour = str_time.split('.')[0]
                minte = str_time.split('.')[1]
                work_end = datetime(year=check_out.year, month=check_out.month, day=check_out.day, hour=00,
                                               minute=00) + timedelta(hours=float(hour), minutes=float(minte))
                work_end = pytz.utc.localize(datetime.strptime(str(work_end), DATETIME_FORMAT)).replace(tzinfo=None)

                if check_out < work_end:
                    dif = work_end - check_out
                    self.early = float(dif.seconds) / 3600

    @api.one
    @api.depends('check_out')
    def _compute_over_time(self):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        if self.check_out and self.employee_id.calendar_id:
            weekend_days = [day.dayofweek for day in self.employee_id.calendar_id.weekend_ids]
            check_in = self._get_check_time(self.check_in).replace(tzinfo=None)
            check_out = self._get_check_time(self.check_out).replace(tzinfo=None)
            if check_out.strftime('%A') not in weekend_days:
                wrok_to = self.get_work_to(check_out, self.employee_id.calendar_id)
                str_time = str(wrok_to)
                hour = str_time.split('.')[0]
                minte = str_time.split('.')[1]
                work_end = datetime(year=check_out.year, month=check_out.month, day=check_out.day, hour=00,
                                               minute=00) + timedelta(hours=float(hour), minutes=float(minte))
                work_end = pytz.utc.localize(datetime.strptime(str(work_end), DATETIME_FORMAT)).replace(tzinfo=None)
                if check_out > work_end:
                    dif = check_out - work_end
                    self.over_time = float(dif.seconds) / 3600
            else:
                dif = check_out - check_in
                self.over_time = float(dif.seconds) / 3600

            if self.employee_id.attendance_id.rule_bonus_ids:
                hour_time = 0.0
                amount_time = 0.0

                time_over = self.get_time_from_float(self.over_time)
                for rule in self.employee_id.attendance_id.rule_bonus_ids:
                    if rule.bonus_type == 'hour':
                        time_from = self.get_time_from_float(rule.time_from)
                        time_to = self.get_time_from_float(rule.time_to)
                        if time_over >= time_from and time_over <= time_to:
                            hour_time += rule.bonus_hours
                    else:
                        start_from = self.get_time_from_float(rule.start)
                        if time_over >= start_from:
                            amount_time += rule.bonus_fixed
                self.over_time_hour = hour_time
                self.over_time_amount = amount_time






