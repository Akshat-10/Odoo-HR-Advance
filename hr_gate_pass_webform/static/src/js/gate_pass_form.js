/** Front-end dynamic behavior for Gate Pass form */
odoo.define('hr_gate_pass_webform.gate_pass_form', function (require) {
    'use strict';

    const publicFormInit = () => {
        const form = document.querySelector('form.oe_gatepass_form');
        if (!form) return;
        const allFieldSelectors = [
            '.field-host', '.field-gate', '.field-department', '.field-representing', '.field-representing-details',
            '.field-contractor-type', '.field-area', '.field-employeeout-reason', '.official-vehicle-wrapper', '.travel-to-wrapper',
            '.field-employeeout-employees', '.field-reason', '.field-returnable', '.field-expected-return'
        ];

        const visibilityMap = {
            visitor: [ 'field-host','field-department','field-representing','field-representing-details','field-reason','field-returnable','field-expected-return' ],
            contractor: [ 'field-department','field-contractor-type','field-area','field-reason','field-returnable','field-expected-return' ],
            material: [ 'field-department','field-reason','field-returnable','field-expected-return' ],
            vehicle: [ 'field-department','field-area','field-reason','field-returnable','field-expected-return' ],
            employee_out: [ 'field-gate','field-employeeout-reason','field-department','field-employeeout-employees','field-reason','field-returnable','field-expected-return' ],
        };

        // Forward declarations (hoisted) to avoid calling before defined
        const toggleEmployeeOut = () => {};
        const toggleReturnable = () => {};

        const toggleFields = () => {
            const passType = form.querySelector('[name=pass_type]').value;
            const showKeys = visibilityMap[passType] || [];
            // Hide all first
            allFieldSelectors.forEach(sel => { form.querySelectorAll('.' + sel.replace('.', '')).forEach(el => el.style.display = 'none'); });
            // Show mapped
            showKeys.forEach(key => form.querySelectorAll('.' + key).forEach(el => el.style.display = '')); 

            // Visitor Details wrapper logic (visitor + contractor per spec)
            const visitorDetails = form.querySelector('.visitor-details-wrapper');
            if (visitorDetails) visitorDetails.style.display = (passType === 'visitor' || passType === 'contractor') ? '' : 'none';

            // Required markers
            const hostReq = form.querySelector('.host-required');
            if (hostReq) hostReq.style.display = (passType === 'visitor') ? 'inline' : 'none';
            const repReq = form.querySelector('.representing-required');
            const repTextReq = form.querySelector('.representing-text-required');
            [repReq, repTextReq].forEach(el => { if (el) el.style.display = (passType === 'visitor') ? 'inline' : 'none'; });

            // Contractor required
            const contractorVisitSelect = form.querySelector('[name=contractor_visit_type]');
            const contractorReq = form.querySelector('.contractor-required');
            if (contractorVisitSelect) contractorVisitSelect.required = (passType === 'contractor');
            if (contractorReq) contractorReq.style.display = (passType === 'contractor') ? 'inline' : 'none';

            // Employee Out reason required marker
            const empOutReq = form.querySelector('.employee-out-reason-required');
            if (empOutReq) empOutReq.style.display = (passType === 'employee_out') ? 'inline' : 'none';

            // Call after definitions replaced below
            if (typeof realToggleEmployeeOut === 'function') realToggleEmployeeOut();
            if (typeof realToggleReturnable === 'function') realToggleReturnable();
        };
        const passTypeSel = form.querySelector('[name=pass_type]');
        passTypeSel && passTypeSel.addEventListener('change', toggleFields);
        toggleFields();

        const returnableChk = form.querySelector('#is_returnable');
    const returnableDate = form.querySelector('.returnable-date');
        const realToggleReturnable = () => {
            if (!returnableChk || !returnableDate) return;
            // Always show the Expected Return field; only toggle required state & asterisk.
            returnableDate.style.display = '';
            const checked = returnableChk.checked;
            const req = returnableDate.querySelector('.return-date-required');
            if (req) req.style.display = checked ? 'inline' : 'none';
            const input = returnableDate.querySelector('input[name=expected_return_date]');
            if (input) input.required = checked;
        };
        returnableChk && returnableChk.addEventListener('change', realToggleReturnable);
        realToggleReturnable();

        // Dynamic add for representing details & ID numbers
        // Dynamic add removed (no longer needed for free text & single ID)

        // Employee Out logic
        const empOutReason = form.querySelector('[name=employee_out_reason]');
        const officialWrapper = form.querySelector('.official-vehicle-wrapper');
        const travelWrapper = form.querySelector('.travel-to-wrapper');
        const officialVehChk = form.querySelector('#official_vehicle_required');
        const travelReqMarker = form.querySelector('.travel-to-required');
        const realToggleEmployeeOut = () => {
            const passType = form.querySelector('[name=pass_type]').value;
            if (passType !== 'employee_out') {
                if (officialWrapper) officialWrapper.style.display = 'none';
                if (travelWrapper) travelWrapper.style.display = 'none';
                return;
            }
            const reason = empOutReason ? empOutReason.value : '';
            // Always show official vehicle checkbox when employee_out; only gate visibility controlled by reason content
            if (officialWrapper) officialWrapper.style.display = '';
            const showTravel = (reason === 'official') && officialVehChk && officialVehChk.checked;
            if (travelWrapper) travelWrapper.style.display = showTravel ? '' : 'none';
            const travelInput = travelWrapper ? travelWrapper.querySelector('input[name=travel_to]') : null;
            if (travelInput) travelInput.required = showTravel;
            if (travelReqMarker) travelReqMarker.style.display = showTravel ? 'inline' : 'none';
        };
        empOutReason && empOutReason.addEventListener('change', realToggleEmployeeOut);
        officialVehChk && officialVehChk.addEventListener('change', realToggleEmployeeOut);
        realToggleEmployeeOut();

        // Department autofill via JSON endpoint (to implement in controller)
        const hostSelect = form.querySelector('[name=host_employee_id]');
        const deptInput = form.querySelector('input[name=department_name]');
        const fetchDept = (empId) => {
            if (!empId) { if (deptInput) deptInput.value=''; return; }
            fetch(`/gatepass/employee/${empId}/department`).then(r=>r.json()).then(data=>{ if (deptInput) deptInput.value = data.department || ''; }).catch(()=>{});
        };
    hostSelect && hostSelect.addEventListener('change', (e)=> fetchDept(e.target.value));
    if (hostSelect && hostSelect.value) fetchDept(hostSelect.value);

    toggleFields();
    const passTypeField = form.querySelector('[name=pass_type]');
    passTypeField && passTypeField.addEventListener('change', toggleFields);

    // Soft UX: indicate training requirement on submit button tooltip
    const submitBtn = form.querySelector('button.btn.btn-primary[type=submit]');
    const trainingBtn = form.querySelector('button[formaction*="create_only=1"]');
    const updateSubmitHint = () => {
        if (!submitBtn) return;
        const pt = (passTypeField && passTypeField.value) || '';
        if ([ 'visitor','contractor','vehicle' ].includes(pt)) {
            submitBtn.title = 'Please click \"Start Safety Training\" and complete it before submitting.';
        } else {
            submitBtn.removeAttribute('title');
        }
    };
    passTypeField && passTypeField.addEventListener('change', updateSubmitHint);
    updateSubmitHint();
    };

    if (document.readyState !== 'loading') {
        publicFormInit();
    } else {
        document.addEventListener('DOMContentLoaded', publicFormInit);
    }
});
