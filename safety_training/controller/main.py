# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class SafetyTrainingController(http.Controller):

    @http.route('/safety_training/start/<int:attempt_id>', type='http', auth='user', website=True)
    def start_training(self, attempt_id, **kwargs):
        """Render the training video player page"""
        attempt = request.env['safety.training.attempt'].sudo().browse(attempt_id)

        if not attempt.exists():
            return request.not_found()

        # Check if user is authorized
        if attempt.user_id.id != request.env.user.id:
            return request.not_found()

        # Start video if not started (and not in failed/retry state)
        if attempt.state == 'video_pending':
            attempt.action_start_video()
        elif attempt.state in ['test_pending', 'failed']:
            # For retry, ensure questions are generated
            if not attempt.selected_question_ids:
                attempt._generate_test_questions()

        # Prepare video URL
        video_url = attempt.video_id.video_url
        if attempt.video_id.video_file:
            # If video file is uploaded, create a route for it
            video_url = '/web/content/safety.training.video/%s/video_file' % attempt.video_id.id

        values = {
            'attempt': attempt,
            'video_url': video_url,
            'video_duration': attempt.video_id.duration,
        }

        return request.render('safety_training.safety_training_video_player', values)

    @http.route('/safety_training/video_started', type='json', auth='user')
    def video_started(self, attempt_id, **kwargs):
        """Log that video playback started"""
        attempt = request.env['safety.training.attempt'].sudo().browse(attempt_id)

        if not attempt.exists() or attempt.user_id.id != request.env.user.id:
            return {'success': False, 'error': 'Invalid attempt'}

        if attempt.state == 'video_pending':
            attempt.action_start_video()

        return {'success': True}

    @http.route('/safety_training/skip_attempt', type='json', auth='user')
    def skip_attempt(self, attempt_id, **kwargs):
        """Log video skip attempt"""
        attempt = request.env['safety.training.attempt'].sudo().browse(attempt_id)

        if not attempt.exists() or attempt.user_id.id != request.env.user.id:
            return {'success': False, 'error': 'Invalid attempt'}

        attempt.action_video_skip_attempt()

        return {
            'success': True,
            'skip_count': attempt.video_skip_attempts
        }

    @http.route('/safety_training/video_complete', type='json', auth='user')
    def video_complete(self, attempt_id, **kwargs):
        """Mark video as completed and prepare quiz"""
        attempt = request.env['safety.training.attempt'].sudo().browse(attempt_id)

        if not attempt.exists() or attempt.user_id.id != request.env.user.id:
            return {'success': False, 'error': 'Invalid attempt'}

        try:
            attempt.action_complete_video()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/safety_training/get_questions', type='json', auth='user')
    def get_questions(self, attempt_id, **kwargs):
        """Get quiz questions for the attempt"""
        attempt = request.env['safety.training.attempt'].sudo().browse(attempt_id)

        if not attempt.exists() or attempt.user_id.id != request.env.user.id:
            return {'success': False, 'error': 'Invalid attempt'}

        # Allow getting questions if video is completed OR if it's a retry
        if not attempt.video_completed and attempt.state not in ['test_pending', 'failed']:
            return {'success': False, 'error': 'Video not completed'}

        # Ensure questions are selected
        if not attempt.selected_question_ids:
            try:
                attempt._generate_test_questions()
            except Exception as e:
                return {'success': False, 'error': str(e)}

        # Start test if in test_pending or failed state
        if attempt.state in ['test_pending', 'failed']:
            try:
                attempt.action_start_test()
            except Exception as e:
                return {'success': False, 'error': str(e)}

        questions = []
        for q in attempt.selected_question_ids:
            questions.append({
                'id': q.id,
                'question': q.question,
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d,
                'category': q.category,
            })

        return {
            'success': True,
            'questions': questions,
            'total': len(questions),
        }

    @http.route('/safety_training/submit_answers', type='json', auth='user')
    def submit_answers(self, attempt_id, answers, **kwargs):
        """Submit quiz answers and get results"""
        attempt = request.env['safety.training.attempt'].sudo().browse(attempt_id)

        if not attempt.exists() or attempt.user_id.id != request.env.user.id:
            return {'success': False, 'error': 'Invalid attempt'}

        # Allow submission for test_in_progress, test_pending, or failed states
        if attempt.state not in ['test_in_progress', 'test_pending', 'failed']:
            return {
                'success': False,
                'error': f'Test not available for submission. Current state: {attempt.state}'
            }

        try:
            # Submit answers - the model will handle state transition
            result = attempt.action_submit_answers(answers)

            # Prepare detailed answer review
            answer_review = []
            for answer in attempt.answer_ids:
                answer_review.append({
                    'question': answer.question_id.question,
                    'selected_answer': answer.selected_answer,
                    'correct_answer': answer.question_id.correct_answer,
                    'is_correct': answer.is_correct,
                    'explanation': answer.question_id.explanation or '',
                })

            return {
                'success': True,
                'passed': result['passed'],
                'score': result['score'],
                'correct_answers': result['correct_answers'],
                'total_questions': result['total_questions'],
                'answers': answer_review,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/safety_training/retry/<int:gate_pass_id>', type='http', auth='user', website=True)
    def retry_training(self, gate_pass_id, **kwargs):
        """Create new attempt and redirect to training"""
        gate_pass = request.env['hr.gate.pass'].sudo().browse(gate_pass_id)

        if not gate_pass.exists():
            return request.not_found()

        # Get latest failed attempt
        failed_attempt = gate_pass.training_attempt_ids.filtered(
            lambda a: not a.passed
        ).sorted('create_date', reverse=True)[:1]

        if failed_attempt:
            new_attempt = failed_attempt.action_retry()
            if 'res_id' in new_attempt:
                return request.redirect('/safety_training/start/%s' % new_attempt['res_id'])

        return request.redirect('/web#id=%s&model=hr.gate.pass&view_type=form' % gate_pass_id)