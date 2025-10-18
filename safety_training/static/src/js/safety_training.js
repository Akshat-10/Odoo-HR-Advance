/** @odoo-module **/

(function() {
    'use strict';

    console.log('Safety Training Script Loading...');

    // Wait for DOM to load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    function init() {
        console.log('Attempting initialization', new Date());

        // Get data from hidden inputs
        const attemptIdInput = document.getElementById('attemptId');
        const videoUrlInput = document.getElementById('videoUrl');
        const videoDurationInput = document.getElementById('videoDuration');

        console.log('Attempt ID Input:', attemptIdInput);
        console.log('Video URL Input:', videoUrlInput);
        console.log('Video Duration Input:', videoDurationInput);

        const attemptId = attemptIdInput ? parseInt(attemptIdInput.value || 0) : 0;
        const videoUrl = videoUrlInput ? videoUrlInput.value : '';
        const videoDuration = videoDurationInput ? parseInt(videoDurationInput.value || 0) : 0;

        console.log('Parsed - Attempt ID:', attemptId, 'Video URL:', videoUrl, 'Duration:', videoDuration);

        if (!attemptId) {
            console.error('Attempt ID not found or invalid');
            alert('Error: Invalid attempt ID');
            return;
        }

        if (!videoUrl) {
            console.error('Video URL not found');
            alert('Error: Video URL not configured');
            return;
        }

        let video = null;
        let questions = [];
        let userAnswers = {};
        let skipAttempts = 0;
        let lastValidTime = 0;
        let videoCompleted = false;

        // Get all sections
        const startSection = document.getElementById('startSection');
        const videoSection = document.getElementById('videoSection');
        const quizSection = document.getElementById('quizSection');
        const resultSection = document.getElementById('resultSection');

        console.log('Sections found:');
        console.log('- Start:', startSection);
        console.log('- Video:', videoSection);
        console.log('- Quiz:', quizSection);
        console.log('- Result:', resultSection);

        // Initialize event listeners
        const startBtn = document.getElementById('startTraining');
        const submitBtn = document.getElementById('submitQuiz');

        if (startBtn) {
            console.log('Start button found, attaching listener');
            startBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('START BUTTON CLICKED!');
                startTraining();
            });
        } else {
            console.error('Start button NOT found');
        }

        if (submitBtn) {
            console.log('Submit button found');
            submitBtn.addEventListener('click', submitQuiz);
        }

        function startTraining() {
            console.log('=== START TRAINING FUNCTION CALLED ===');

            if (startSection) {
                console.log('Hiding start section');
                startSection.style.display = 'none';
            } else {
                console.error('Start section not found!');
            }

            if (videoSection) {
                console.log('Showing video section');
                videoSection.style.display = 'block';
            } else {
                console.error('Video section not found!');
            }

            // Wait a bit for DOM to update
            setTimeout(function() {
                console.log('Initializing video after timeout');
                initVideo();
            }, 200);
        }

        function initVideo() {
            console.log('=== INIT VIDEO FUNCTION CALLED ===');

            video = document.getElementById('safetyVideo');

            if (!video) {
                console.error('ERROR: Video element not found in DOM!');
                console.log('Trying to find video in videoSection:', videoSection);
                if (videoSection) {
                    const allVideos = videoSection.getElementsByTagName('video');
                    console.log('Found videos in section:', allVideos);
                    if (allVideos.length > 0) {
                        video = allVideos[0];
                        console.log('Using first video element found');
                    }
                }

                if (!video) {
                    alert('Error: Video player not found. Please refresh the page.');
                    return;
                }
            }

            console.log('Video element:', video);
            console.log('Video display style:', window.getComputedStyle(video).display);
            console.log('Video visibility:', window.getComputedStyle(video).visibility);

            // Get video source
            const source = video.querySelector('source');
            console.log('Video source element:', source);
            console.log('Video source URL:', source ? source.src : 'NO SOURCE');

            // Ensure video has source
            if (source && (!source.src || source.src === '')) {
                console.log('Setting video source to:', videoUrl);
                source.src = videoUrl;
                video.load();
            }

            // Video error handling
            video.addEventListener('error', function(e) {
                console.error('VIDEO ERROR EVENT:', e);
                console.error('Video error code:', video.error?.code);
                console.error('Video error message:', video.error?.message);

                let errorMsg = 'Error loading video. ';
                if (video.error) {
                    switch(video.error.code) {
                        case 1: errorMsg += 'Loading aborted.'; break;
                        case 2: errorMsg += 'Network error.'; break;
                        case 3: errorMsg += 'Decoding failed.'; break;
                        case 4: errorMsg += 'Video format not supported.'; break;
                        default: errorMsg += 'Unknown error.';
                    }
                }
                alert(errorMsg + '\nPlease check if the video file exists at: ' + videoUrl);
            });

            // Video loaded successfully
            video.addEventListener('loadedmetadata', function() {
                console.log('✓ Video metadata loaded successfully');
                console.log('Video duration:', video.duration, 'seconds');
            });

            video.addEventListener('loadeddata', function() {
                console.log('✓ Video data loaded');
            });

            video.addEventListener('canplay', function() {
                console.log('✓ Video can play');
            });

            video.addEventListener('canplaythrough', function() {
                console.log('✓ Video can play through');
            });

            // Disable right-click
            video.addEventListener('contextmenu', function(e) {
                e.preventDefault();
            });

            // Prevent seeking forward - STRICT MODE
            video.addEventListener('seeking', function() {
                const currentTime = video.currentTime;
                console.log('Seeking detected - Trying to go to:', currentTime, 'Last Valid:', lastValidTime);

                // If trying to skip ahead (with small tolerance for buffering)
                if (!videoCompleted && currentTime > lastValidTime + 0.5) {
                    skipAttempts++;
                    console.warn('SKIP ATTEMPT BLOCKED! Count:', skipAttempts);

                    // Pause the video
                    video.pause();

                    // Show warning
                    showSkipWarning();

                    // Reset to beginning
                    video.currentTime = 0;
                    lastValidTime = 0;
                    updateProgress(0);

                    // Restart video after a brief delay
                    setTimeout(function() {
                        video.play().catch(function(err) {
                            console.error('Error restarting video:', err);
                        });
                    }, 500);
                }
            });

            // Additional protection: prevent manual time changes
            video.addEventListener('seeked', function() {
                if (!videoCompleted && video.currentTime > lastValidTime + 0.5) {
                    console.warn('Seeked event blocked');
                    video.currentTime = lastValidTime;
                }
            });

            // Track progress
            video.addEventListener('timeupdate', function() {
                if (video.currentTime > lastValidTime) {
                    lastValidTime = video.currentTime;
                }
                const progress = (video.currentTime / video.duration) * 100;
                updateProgress(progress);
            });

            // Video ended
            video.addEventListener('ended', function() {
                console.log('✓ Video playback ended');
                videoCompleted = true;
                onVideoComplete();
            });

            // Handle video overlay
            const overlay = document.getElementById('videoOverlay');
            if (overlay) {
                console.log('Video overlay found, attaching click listener');
                overlay.addEventListener('click', function() {
                    console.log('Overlay clicked - attempting to play video');
                    this.style.display = 'none';

                    const playPromise = video.play();

                    if (playPromise !== undefined) {
                        playPromise.then(function() {
                            console.log('✓ Video playing successfully');
                            notifyVideoStarted();
                        }).catch(function(error) {
                            console.error('Play error:', error);
                            alert('Error playing video: ' + error.message);
                        });
                    } else {
                        console.log('Video play() returned undefined');
                        notifyVideoStarted();
                    }
                });
            } else {
                console.warn('Video overlay not found - video will be visible immediately');
            }

            console.log('=== VIDEO INITIALIZATION COMPLETE ===');
        }

        function updateProgress(percent) {
            const progressBar = document.getElementById('videoProgress');
            if (progressBar) {
                progressBar.style.width = percent + '%';
                progressBar.textContent = Math.round(percent) + '%';
            }
        }

        function showSkipWarning() {
            const skipCount = document.getElementById('skipCount');
            if (skipCount) {
                skipCount.textContent = skipAttempts;
            }
            const warning = document.getElementById('skipWarning');
            if (warning) {
                warning.style.display = 'block';
                setTimeout(function() {
                    warning.style.display = 'none';
                }, 3000);
            }
            notifySkipAttempt();
        }

        function onVideoComplete() {
            console.log('Processing video completion...');
            callJsonRpc('/safety_training/video_complete', {
                attempt_id: attemptId
            }).then(data => {
                console.log('Video complete response:', data);
                if (data && data.success) {
                    loadQuiz();
                } else {
                    console.error('Video completion failed:', data);
                    alert('Error completing video. Please try again.');
                }
            }).catch(error => {
                console.error('Error completing video:', error);
                alert('Error completing video. Please try again.');
            });
        }

        function loadQuiz() {
            console.log('Loading quiz...');
            if (videoSection) videoSection.style.display = 'none';
            if (quizSection) quizSection.style.display = 'block';

            callJsonRpc('/safety_training/get_questions', {
                attempt_id: attemptId
            }).then(data => {
                console.log('Questions received:', data);
                if (data && data.success) {
                    questions = data.questions;
                    renderQuestions();
                } else {
                    console.error('Failed to load questions:', data);
                    alert('Error loading questions. Please try again.');
                }
            }).catch(error => {
                console.error('Error loading questions:', error);
                alert('Error loading questions. Please try again.');
            });
        }

        function renderQuestions() {
            const container = document.getElementById('questionsContainer');
            if (!container) return;

            container.innerHTML = '';

            const totalQuestionsSpan = document.getElementById('totalQuestions');
            if (totalQuestionsSpan) {
                totalQuestionsSpan.textContent = questions.length;
            }

            questions.forEach(function(q, index) {
                const questionDiv = document.createElement('div');
                questionDiv.className = 'question-card';
                questionDiv.innerHTML = `
                    <div class="question-text">
                        <strong>Question ${index + 1}:</strong> ${escapeHtml(q.question)}
                    </div>
                    <div class="option-group">
                        <label class="option-label">
                            <input type="radio" name="question_${q.id}" value="a" required/>
                            <strong>A)</strong> ${escapeHtml(q.option_a)}
                        </label>
                        <label class="option-label">
                            <input type="radio" name="question_${q.id}" value="b" required/>
                            <strong>B)</strong> ${escapeHtml(q.option_b)}
                        </label>
                        <label class="option-label">
                            <input type="radio" name="question_${q.id}" value="c" required/>
                            <strong>C)</strong> ${escapeHtml(q.option_c)}
                        </label>
                        <label class="option-label">
                            <input type="radio" name="question_${q.id}" value="d" required/>
                            <strong>D)</strong> ${escapeHtml(q.option_d)}
                        </label>
                    </div>
                `;
                container.appendChild(questionDiv);
            });

            // Handle option selection
            const labels = document.querySelectorAll('.option-label');
            labels.forEach(function(label) {
                label.addEventListener('click', function() {
                    const radio = this.querySelector('input[type="radio"]');
                    radio.checked = true;
                    const siblings = this.parentElement.querySelectorAll('.option-label');
                    siblings.forEach(function(s) {
                        s.classList.remove('selected');
                    });
                    this.classList.add('selected');
                });
            });
        }

        function submitQuiz() {
            console.log('Submitting quiz...');
            userAnswers = {};
            let allAnswered = true;

            questions.forEach(function(q) {
                const selected = document.querySelector('input[name="question_' + q.id + '"]:checked');
                if (selected) {
                    userAnswers[q.id] = selected.value;
                } else {
                    allAnswered = false;
                }
            });

            if (!allAnswered) {
                alert('Please answer all questions before submitting.');
                return;
            }

            callJsonRpc('/safety_training/submit_answers', {
                attempt_id: attemptId,
                answers: userAnswers
            }).then(data => {
                console.log('Submit response:', data);
                if (data && data.success) {
                    showResults(data);
                } else {
                    console.error('Submit failed:', data);
                    alert('Error submitting answers. Please try again.');
                }
            }).catch(error => {
                console.error('Error submitting answers:', error);
                alert('Error submitting answers. Please try again.');
            });
        }

        function showResults(result) {
            if (quizSection) quizSection.style.display = 'none';
            if (resultSection) resultSection.style.display = 'block';

            const passedClass = result.passed ? 'result-passed' : 'result-failed';
            const iconClass = result.passed ? 'fa-check-circle text-success' : 'fa-times-circle text-danger';
            const iconColor = result.passed ? '#28a745' : '#dc3545';

            let resultHtml = `
                <div class="${passedClass}">
                    <div class="result-icon">
                        <i class="fa ${iconClass}" style="color: ${iconColor}"></i>
                    </div>
                    <h2>${result.passed ? 'Congratulations!' : 'Training Not Passed'}</h2>
                    <div class="result-score" style="color: ${iconColor}">
                        ${result.score.toFixed(1)}%
                    </div>
                    <p class="lead">
                        You answered ${result.correct_answers} out of ${result.total_questions} questions correctly.
                    </p>
            `;

            if (result.passed) {
                resultHtml += `
                    <div class="alert alert-success mt-4">
                        <p><strong>You have successfully completed the safety training!</strong></p>
                        <p>You can now proceed with your gate pass submission.</p>
                    </div>
                    <button onclick="window.close()" class="btn btn-success btn-lg">
                        <i class="fa fa-check"></i> Complete Training
                    </button>
                `;
            } else {
                resultHtml += `
                    <div class="alert alert-danger mt-4">
                        <p><strong>You need at least 80% to pass.</strong></p>
                        <p>You must watch the video and take the assessment again.</p>
                    </div>
                    <button onclick="location.reload()" class="btn btn-danger btn-lg">
                        <i class="fa fa-refresh"></i> Retry Training
                    </button>
                `;
            }

            resultHtml += '<div class="mt-5"><h3>Answer Review</h3>';
            result.answers.forEach(function(ans, index) {
                const isCorrect = ans.is_correct;
                const badgeClass = isCorrect ? 'badge-success' : 'badge-danger';
                resultHtml += `
                    <div class="question-card">
                        <div class="question-text">
                            <strong>Question ${index + 1}:</strong> ${escapeHtml(ans.question)}
                            <span class="badge ${badgeClass}" style="float: right;">
                                ${isCorrect ? 'Correct' : 'Incorrect'}
                            </span>
                        </div>
                        <p><strong>Your answer:</strong> ${ans.selected_answer.toUpperCase()}</p>
                        <p><strong>Correct answer:</strong> ${ans.correct_answer.toUpperCase()}</p>
                        ${ans.explanation ? `<div class="explanation-box"><strong>Explanation:</strong> ${escapeHtml(ans.explanation)}</div>` : ''}
                    </div>
                `;
            });
            resultHtml += '</div></div>';

            const resultContent = document.getElementById('resultContent');
            if (resultContent) {
                resultContent.innerHTML = resultHtml;
            }
        }

        function notifyVideoStarted() {
            callJsonRpc('/safety_training/video_started', {
                attempt_id: attemptId
            }).then(data => {
                console.log('Video started notification sent:', data);
            }).catch(error => {
                console.error('Error notifying video start:', error);
            });
        }

        function notifySkipAttempt() {
            callJsonRpc('/safety_training/skip_attempt', {
                attempt_id: attemptId
            }).catch(error => {
                console.error('Error notifying skip:', error);
            });
        }

        function callJsonRpc(url, params) {
            console.log('JSON-RPC call to:', url, 'with params:', params);
            return fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: params
                })
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.error) {
                    throw new Error(data.error.message || 'Unknown error');
                }
                return data.result;
            });
        }

        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }

        console.log('=== Safety Training Script Initialized ===');
    }
})();