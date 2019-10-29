# -*- coding: utf-8 -*-


import logging
import math
from datetime import timedelta
from werkzeug import url_encode

from openerp import api, fields, models
from openerp.exceptions import UserError, AccessError, ValidationError
from openerp.tools import float_compare
from openerp.tools.translate import _
from datetime import datetime,date

_logger = logging.getLogger(__name__)


HOURS_PER_DAY = 8



class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    @api.model
    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        from_dt = fields.Datetime.from_string(date_from)
        to_dt = fields.Datetime.from_string(date_to)

        tomorow_date =date.today() + timedelta(days=1)
        dif_date = tomorow_date - date.today()
        print(dif_date)

        # if employee_id:
        #     employee = self.env['hr.employee'].browse(employee_id)
        #     resource = employee.resource_id.sudo()
        #     if resource and resource.calendar_id:
        #         hours = resource.calendar_id.get_working_hours(from_dt, to_dt, resource_id=resource.id,
        #                                                        compute_leaves=True)
        #         uom_hour = resource.calendar_id.uom_id
        #         uom_day = self.env.ref('product.product_uom_day')
        #         if uom_hour and uom_day:
        #             return uom_hour._compute_quantity(hours, uom_day)

        if to_dt > from_dt:
            time_delta = (to_dt - from_dt) + dif_date
        if to_dt == from_dt:
            time_delta = dif_date
        return math.ceil(time_delta.days + float(time_delta.seconds) / 86400)

    @api.model
    @api.onchange('date_from')
    def _onchange_date_from(self):
        """ If there are no date set for date_to, automatically set one 8 hours later than
            the date_from. Also update the number_of_days.
        """
        date_from = self.date_from
        date_to = self.date_to

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            date_to_with_delta = fields.Datetime.from_string(date_from) + timedelta(hours=HOURS_PER_DAY)
            self.date_to = str(date_to_with_delta)

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            self.number_of_days_temp = self._get_number_of_days(date_from, date_to, self.employee_id.id)

        # if (date_to and date_from) and (date_from == date_to):
        #     self.number_of_days_temp = 1

        else:
            self.number_of_days_temp = 0


    def _default_company(self):
        return self.env['res.company']._company_default_get('res.partner')

    date_from = fields.Date('Start Date', readonly=True, index=True, copy=False,
                                states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    date_to = fields.Date('End Date', readonly=True, copy=False,
                              states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})

    company_id = fields.Many2one('res.company', 'Company', index=True, default=_default_company)





    def send_mail(self,obj_id, subject, email_to, body_html):
        values = {}
        ir_model_data = self.env['ir.model.data']
        template = \
            ir_model_data.get_object_reference('shah_hr_custom', 'holidays_send_mail')[1]
        # print '-------------------------', template

        email_template_obj = self.env['mail.template']

        template_ids = email_template_obj.browse(template)
        # print '-------------------------', template_ids
        object = self.env['hr.holidays'].browse(obj_id).sudo()
        employee = ""
        if object.employee_id.name:
            employee = object.employee_id.name

        
        values['name'] = template_ids.name
        values['subject'] = subject
        values['model_id'] = template_ids.model_id
        values['email_from'] = object.company_id.email or ''
        values['lang'] = template_ids.lang
        values['auto_delete'] = True
        values['email_to'] = email_to.email
        values['body_html'] = \
            u"".join(u'<![CDATA["<div style="text-align: right;direction:rtl">' +
                     u'<p dir="rtl" style="text-align: right"> Dear %s </p>' % (email_to.name) +
                     u'<p style="font-size: 1.1em;text-align: right">Kindly Approve</p>' +
                     u'<br/><br/>' +
                     u'<p dir="rtl" style="text-align: right">' + u'Leave Type:%s' % (object.name) + u' </p>' +
                     u'<br/>' +
                     u'<p dir="rtl" style="text-align: right"> Leave Requester:%s  </p>' % (employee) +
                     u'<br/>' +
                     u'<p style="font-size: 1.1em;text-align: right;">' +
                     u'</p></div>')
        values['body'] = template_ids.body_html
        values['res_id'] = False
        mail_mail_obj = self.env['mail.mail']
        msg_id = mail_mail_obj.create(values)
        if msg_id:
            mail_mail_obj.send([msg_id])
        return True


    @api.model
    def create(self, values):

        res =  super(HrHolidays, self).create(values)
        template = self.env.ref('shah_hr_custom.holidays_send_mail', False)
        for rec in self.env['res.users'].search([]).filtered(
                lambda user: user.has_group('hr_holidays.group_hr_holidays_manager')).mapped('partner_id'):
            if not template:
                return
            subject = "Leave request is created"
            email_to = rec
            body_html = template.body_html
            self.send_mail(res.id, subject, email_to, body_html)
        return res

    @api.multi
    def action_approve(self):

        res = super(HrHolidays, self).action_approve()
        template = self.env.ref('shah_hr_custom.holidays_send_mail', False)
        for rec in self.env['res.users'].search([]).filtered(
                lambda user: user.has_group('hr_holidays.group_hr_holidays_manager')).mapped('partner_id'):
            if not template:
                return
            subject = "Leave request is approved"
            email_to = rec
            body_html = template.body_html
            self.send_mail(self.id, subject, email_to, body_html)

        return res

    @api.multi
    def action_validate(self):
        res = super(HrHolidays, self).action_validate()
        template = self.env.ref('shah_hr_custom.holidays_send_mail', False)
        for rec in self.env['res.users'].search([]).filtered(
                lambda user: user.has_group('hr_holidays.group_hr_holidays_manager')).mapped('partner_id'):
            if not template:
                return
            subject = "Leave request is approved"
            email_to = rec
            body_html = template.body_html
            self.send_mail(self.id, subject, email_to, body_html)

        return res

    @api.multi
    def action_refuse(self):
        res = super(HrHolidays, self).action_refuse()
        template = self.env.ref('shah_hr_custom.holidays_send_mail', False)
        for rec in self.env['res.users'].search([]).filtered(
                lambda user: user.has_group('hr_holidays.group_hr_holidays_manager')).mapped('partner_id'):
            if not template:
                return
            subject = "Leave request is rejected"
            email_to = rec
            body_html = template.body_html
            self.send_mail(self.id, subject, email_to, body_html)

        return res

   
