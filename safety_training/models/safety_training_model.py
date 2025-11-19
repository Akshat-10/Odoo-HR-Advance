# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
import random
import json
import uuid


class SafetyTrainingVideo(models.Model):
    _name = 'safety.training.video'
    _description = 'Safety Training Video'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Video Title', required=True)
    description = fields.Text(string='Description')
    video_url = fields.Char(string='Video URL', required=True, help='URL or path to the video file')
    video_file = fields.Binary(string='Video File', attachment=True)
    duration = fields.Integer(string='Duration (seconds)', required=True)
    pass_type = fields.Selection([
        ('employee_out', 'Employee Out'),
        ('visitor', 'Visitor'),
        ('material', 'Material'),
        ('vehicle', 'Vehicle'),
        ('contractor', 'Contractor')
    ], string='Pass Type', required=True)
    active = fields.Boolean(string='Active', default=True)
    question_ids = fields.One2many('safety.training.question', 'video_id', string='Questions')
    pass_percentage = fields.Float(string='Pass Percentage', default=80.0, help='Minimum percentage to pass')
    total_questions_per_test = fields.Integer(string='Questions Per Test', default=5)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )


class SafetyTrainingQuestion(models.Model):
    _name = 'safety.training.question'
    _description = 'Safety Training Question'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    video_id = fields.Many2one('safety.training.video', string='Video', required=True, ondelete='cascade')
    question = fields.Text(string='Question', required=True)
    option_a = fields.Char(string='Option A', required=True)
    option_b = fields.Char(string='Option B', required=True)
    option_c = fields.Char(string='Option C', required=True)
    option_d = fields.Char(string='Option D', required=True)
    correct_answer = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('d', 'D')
    ], string='Correct Answer', required=True)
    explanation = fields.Text(string='Explanation')
    active = fields.Boolean(string='Active', default=True)
    category = fields.Selection([
        ('ppe', 'PPE Requirements'),
        ('safety', 'Safety Instructions'),
        ('emergency', 'Emergency Procedures'),
        ('prohibited', 'Prohibited Activities'),
        ('general', 'General Safety')
    ], string='Category', default='general')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )


class SafetyTrainingAttempt(models.Model):
    _name = 'safety.training.attempt'
    _description = 'Safety Training Attempt'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    gate_pass_id = fields.Many2one('hr.gate.pass', string='Gate Pass', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True)
    video_id = fields.Many2one('safety.training.video', string='Video', required=True)

    # Video tracking
    video_started_at = fields.Datetime(string='Video Started At')
    video_completed_at = fields.Datetime(string='Video Completed At')
    video_watch_duration = fields.Integer(string='Watch Duration (seconds)', default=0)
    video_completed = fields.Boolean(string='Video Completed', default=False)
    video_skip_attempts = fields.Integer(string='Skip Attempts', default=0)

    # Assessment tracking
    test_started_at = fields.Datetime(string='Test Started At')
    test_completed_at = fields.Datetime(string='Test Completed At')
    answer_ids = fields.One2many('safety.training.answer', 'attempt_id', string='Answers')
    score = fields.Float(string='Score (%)', compute='_compute_score', store=True)
    total_questions = fields.Integer(string='Total Questions')
    correct_answers = fields.Integer(string='Correct Answers', compute='_compute_score', store=True)
    passed = fields.Boolean(string='Passed', compute='_compute_score', store=True)

    state = fields.Selection([
        ('video_pending', 'Video Pending'),
        ('video_watching', 'Watching Video'),
        ('test_pending', 'Test Pending'),
        ('test_in_progress', 'Test In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='State', default='video_pending')

    attempt_number = fields.Integer(string='Attempt Number', default=1)
    selected_question_ids = fields.Many2many('safety.training.question', string='Selected Questions')
    access_token = fields.Char(string='Access Token', copy=False, index=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.depends('answer_ids', 'answer_ids.is_correct', 'total_questions')
    def _compute_score(self):
        for rec in self:
            if rec.total_questions > 0:
                correct = len(rec.answer_ids.filtered(lambda a: a.is_correct))
                rec.correct_answers = correct
                rec.score = (correct / rec.total_questions) * 100
                rec.passed = rec.score >= rec.video_id.pass_percentage
            else:
                rec.correct_answers = 0
                rec.score = 0.0
                rec.passed = False

    @api.model_create_multi
    def create(self, vals_list):
        # Support both single dict and list of dicts
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        for vals in vals_list:
            if not vals.get('access_token'):
                vals['access_token'] = uuid.uuid4().hex
        records = super().create(vals_list)
        return records

    def action_start_video(self):
        """Start video watching"""
        self.ensure_one()
        self.write({
            'video_started_at': fields.Datetime.now(),
            'state': 'video_watching',
            'video_watch_duration': 0,
            'video_skip_attempts': 0,
        })
        return True

    def action_video_skip_attempt(self):
        """Log skip attempt - will restart video"""
        self.ensure_one()
        self.video_skip_attempts += 1
        return True

    def action_complete_video(self):
        """Mark video as completed"""
        self.ensure_one()
        if not self.video_completed:
            self.write({
                'video_completed_at': fields.Datetime.now(),
                'video_completed': True,
                'state': 'test_pending',
            })
            # Generate random questions for test
            self._generate_test_questions()
        return True

    def _generate_test_questions(self):
        """Generate random questions for the test"""
        self.ensure_one()
        all_questions = self.video_id.question_ids.filtered(lambda q: q.active)
        if len(all_questions) < self.video_id.total_questions_per_test:
            raise UserError(_('Not enough questions available. Need at least %s questions.' %
                              self.video_id.total_questions_per_test))

        # Randomly select questions
        selected = random.sample(all_questions.ids, self.video_id.total_questions_per_test)
        self.write({
            'selected_question_ids': [(6, 0, selected)],
            'total_questions': len(selected),
        })

    def action_start_test(self):
        """Start the assessment test"""
        self.ensure_one()
        if not self.video_completed:
            raise UserError(_('Please complete watching the video first.'))

        # Clear any previous answers for retry scenarios
        if self.answer_ids:
            self.answer_ids.unlink()

        self.write({
            'test_started_at': fields.Datetime.now(),
            'state': 'test_in_progress',
            'test_completed_at': False,  # Reset completion time
        })
        return True

    def action_submit_answers(self, answers_data):
        """
        Submit test answers
        answers_data: dict like {question_id: selected_option, ...}
        """
        self.ensure_one()

        # Allow submission if test is in progress OR if it's a retry (test_pending or failed state)
        if self.state not in ['test_in_progress', 'test_pending', 'failed']:
            raise UserError(_('Test is not available for submission. Current state: %s') % self.state)

        # If state is test_pending or failed, start the test first
        if self.state in ['test_pending', 'failed']:
            self.action_start_test()

        # Clear any existing answers (for retry case)
        if self.answer_ids:
            self.answer_ids.unlink()

        # Create answer records
        Answer = self.env['safety.training.answer']
        for question_id, selected_option in answers_data.items():
            question = self.env['safety.training.question'].browse(int(question_id))
            is_correct = question.correct_answer == selected_option

            Answer.create({
                'attempt_id': self.id,
                'question_id': question.id,
                'selected_answer': selected_option,
                'is_correct': is_correct,
            })

        # Complete test
        self.write({
            'test_completed_at': fields.Datetime.now(),
            'state': 'completed' if self.passed else 'failed',
        })

        return {
            'passed': self.passed,
            'score': self.score,
            'correct_answers': self.correct_answers,
            'total_questions': self.total_questions,
        }

    def action_retry(self):
        """Create new attempt for retry"""
        self.ensure_one()
        if self.passed:
            raise UserError(_('You have already passed the assessment.'))

        new_attempt = self.create({
            'gate_pass_id': self.gate_pass_id.id,
            'user_id': self.user_id.id,
            'video_id': self.video_id.id,
            'attempt_number': self.attempt_number + 1,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'safety.training.attempt',
            'res_id': new_attempt.id,
            'view_mode': 'form',
            'target': 'current',
        }


class SafetyTrainingAnswer(models.Model):
    _name = 'safety.training.answer'
    _description = 'Safety Training Answer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    attempt_id = fields.Many2one('safety.training.attempt', string='Attempt', required=True, ondelete='cascade')
    question_id = fields.Many2one('safety.training.question', string='Question', required=True)
    selected_answer = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('d', 'D')
    ], string='Selected Answer', required=True)
    is_correct = fields.Boolean(string='Correct', default=False)
    answered_at = fields.Datetime(string='Answered At', default=fields.Datetime.now)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )


class HrGatePass(models.Model):
    _inherit = 'hr.gate.pass'

    training_required = fields.Boolean(string='Training Required', compute='_compute_training_required', store=True)
    training_completed = fields.Boolean(string='Training Completed', default=False)
    training_attempt_ids = fields.One2many('safety.training.attempt', 'gate_pass_id', string='Training Attempts')
    latest_training_attempt_id = fields.Many2one('safety.training.attempt',
                                                 string='Latest Attempt',
                                                 compute='_compute_latest_attempt')
    training_passed = fields.Boolean(string='Training Passed', compute='_compute_training_status', store=True)

    @api.depends('pass_type')
    def _compute_training_required(self):
        for rec in self:
            # Training required for visitor, contractor, and vehicle types
            rec.training_required = rec.pass_type in ['visitor', 'contractor', 'vehicle']

    @api.depends('training_attempt_ids', 'training_attempt_ids.state', 'training_attempt_ids.passed')
    def _compute_training_status(self):
        for rec in self:
            passed_attempts = rec.training_attempt_ids.filtered(lambda a: a.passed)
            rec.training_passed = bool(passed_attempts)
            rec.training_completed = rec.training_passed

    def _compute_latest_attempt(self):
        for rec in self:
            rec.latest_training_attempt_id = rec.training_attempt_ids[:1] if rec.training_attempt_ids else False

    def action_start_training(self):
        """Start or continue safety training"""
        self.ensure_one()

        # Get video for this pass type
        video = self.env['safety.training.video'].search([
            ('pass_type', '=', self.pass_type),
            ('active', '=', True)
        ], limit=1)

        if not video:
            raise UserError(_('No training video configured for this pass type.'))

        # Check if there's an ongoing attempt that hasn't been completed or failed
        ongoing = self.training_attempt_ids.filtered(
            lambda a: a.state in ['video_pending', 'video_watching']
        )

        if ongoing:
            attempt = ongoing[0]
        else:
            # For retry case, check if there's a failed attempt that needs questions
            failed_attempt = self.training_attempt_ids.filtered(
                lambda a: a.state in ['test_pending', 'failed']
            )

            if failed_attempt:
                # Reuse the failed attempt for retry
                attempt = failed_attempt[0]
                # Reset state to allow taking test again
                attempt.write({
                    'state': 'test_pending',
                    'test_started_at': False,
                    'test_completed_at': False,
                })
            else:
                # Create new attempt
                attempt = self.env['safety.training.attempt'].create({
                    'gate_pass_id': self.id,
                    'video_id': video.id,
                    'attempt_number': len(self.training_attempt_ids) + 1,
                })

        # Return action to open in new window/tab, include token for public access
        url = '/safety_training/start/%s?token=%s' % (attempt.id, attempt.access_token or '')
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_submit(self):
        """Override submit to check training completion"""
        for rec in self:
            if rec.training_required and not rec.training_passed:
                raise UserError(_('Please complete the safety training before submitting the gate pass.'))
        return super(HrGatePass, self).action_submit()