"""
Copyright ©2024. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""

import pytest
from xena.models.email_template import EmailTemplate
from xena.models.email_template_type import EmailTemplateType
from xena.models.term import Term
from xena.pages.email_templates_page import EmailTemplatesPage
from xena.test_utils import util

util.reset_email_template_test_data(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START)


@pytest.mark.usefixtures('page_objects')
class TestEmailTemplates:

    term = Term()
    template = EmailTemplate(
        template_type=EmailTemplateType.INSTR_ANNUNCIATION_SEM_START,
        subject='Welcome to Course Capture <code>term.name</code>',
        body='',
    )

    def test_log_in(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_email_templates_link()

    def test_template_options(self):
        self.templates_page.click_template_select()
        options = self.templates_page.visible_menu_options()
        options.sort()
        types = [templ.value['desc'] for templ in EmailTemplateType]
        types.sort()
        assert options == types

    def test_create_template_cancel(self):
        self.templates_page.click_menu_option(self.template.template_type.value['desc'])
        self.templates_page.click_cancel()

    def test_create_template_name_input(self):
        self.templates_page.click_template_select()
        self.templates_page.click_menu_option(self.template.template_type.value['desc'])
        self.templates_page.enter_template_name('Semester start')

    def test_create_template_subj_input(self):
        self.templates_page.enter_subject(self.template.subject)
        self.template.subject = f'Welcome to Course Capture {self.term.name}'

    def test_create_template_show_codes(self):
        self.templates_page.click_template_codes_button()
        for code in EmailTemplatesPage.template_codes():
            assert code in self.templates_page.template_codes_text()

    def test_create_template_enter_codes(self):
        self.templates_page.click_close_template_codes_button()
        self.templates_page.enter_all_codes_in_body()

    def test_create_template_save_template(self):
        self.templates_page.click_save()

    def test_pre_existing_template(self):
        self.templates_page.click_template_select()
        assert self.templates_page.is_menu_option_disabled(self.template.template_type.value['desc'])

    def test_edit_template_cancel(self):
        self.templates_page.hit_escape()
        self.templates_page.click_edit_template_link(self.template)
        self.templates_page.click_cancel()

    def test_edit_template_save(self):
        self.templates_page.click_edit_template_link(self.template)
        self.templates_page.click_save()

    def test_delete_button(self):
        self.templates_page.load_page()
        self.templates_page.click_delete_template_button(self.template)
        assert not self.templates_page.is_template_row_present(self.template)

    def test_restore_template(self):
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_ANNUNCIATION_SEM_START,
            subject='Welcome to <code>term.name</code> Course Capture <code>recipient.name</code>',
            body='',
        )
        self.templates_page.create_template(template)

    def test_admin_operator_requested(self):
        util.reset_email_template_test_data(EmailTemplateType.ADMIN_OPERATOR_REQUESTED)
        template = EmailTemplate(
            template_type=EmailTemplateType.ADMIN_OPERATOR_REQUESTED,
            subject='Admin alert: <code>course.name</code> operator requested',
            body='',
        )
        self.templates_page.create_template(template)

    def test_instructors_added(self):
        util.reset_email_template_test_data(EmailTemplateType.INSTR_ADDED)
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_ADDED,
            subject='<code>course.name</code> Instructor(s) added to class',
            body='',
        )
        self.templates_page.create_template(template)

    def test_instructor_new_class_scheduled(self):
        util.reset_email_template_test_data(EmailTemplateType.INSTR_ANNUNCIATION_NEW_COURSE_SCHED)
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_ANNUNCIATION_NEW_COURSE_SCHED,
            subject='<code>course.name</code> has been scheduled',
            body='',
        )
        self.templates_page.create_template(template)

    def test_instructor_remind_scheduled(self):
        util.reset_email_template_test_data(EmailTemplateType.INSTR_ANNUNCIATION_REMINDER)
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_ANNUNCIATION_REMINDER,
            subject='<code>recipient.name</code>: you have <code>term.name</code> classes scheduled for recording',
            body='',
        )
        self.templates_page.create_template(template)

    def test_instr_semester_start(self):
        util.reset_email_template_test_data(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START)
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_ANNUNCIATION_SEM_START,
            subject='Welcome to <code>term.name</code> Course Capture <code>recipient.name</code>',
            body='',
        )
        self.templates_page.create_template(template)

    def test_instr_changes_confirmed(self):
        util.reset_email_template_test_data(EmailTemplateType.INSTR_CHANGES_CONFIRMED)
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_CHANGES_CONFIRMED,
            subject='<code>course.name</code> changes confirmed',
            body='',
        )
        self.templates_page.create_template(template)

    def test_instr_no_longer_scheduled(self):
        util.reset_email_template_test_data(EmailTemplateType.INSTR_COURSE_CANCELLED)
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_COURSE_CANCELLED,
            subject='<code>course.name</code>, we regret to inform you',
            body='',
        )
        self.templates_page.create_template(template)

    def test_instr_opted_out(self):
        util.reset_email_template_test_data(EmailTemplateType.INSTR_OPTED_OUT)
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_OPTED_OUT,
            subject='<code>recipient.name</code> you have opted out of Course Capture',
            body='',
        )
        self.templates_page.create_template(template)

    def test_instr_instructors_removed(self):
        util.reset_email_template_test_data(EmailTemplateType.INSTR_REMOVED)
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_REMOVED,
            subject='<code>course.name</code> instructor(s) removed from class',
            body='',
        )
        self.templates_page.create_template(template)

    def test_instr_room_change_no_longer_eligible(self):
        util.reset_email_template_test_data(EmailTemplateType.INSTR_ROOM_CHANGE_INELIGIBLE)
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_ROOM_CHANGE_INELIGIBLE,
            subject='Your course <code>course.name</code> is no longer eligible for course capture',
            body='',
        )
        self.templates_page.create_template(template)

    def test_instr_schedule_change(self):
        util.reset_email_template_test_data(EmailTemplateType.INSTR_SCHEDULE_CHANGE)
        template = EmailTemplate(
            template_type=EmailTemplateType.INSTR_SCHEDULE_CHANGE,
            subject='Changes to your Course Capture schedule for <code>course.name</code>',
            body='',
        )
        self.templates_page.create_template(template)
