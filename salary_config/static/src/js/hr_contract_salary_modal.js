/** @odoo-module **/

import SalaryPackageWidget from "@hr_contract_salary/js/hr_contract_salary";
import { renderToElement } from "@web/core/utils/render";
import { rpc } from "@web/core/network/rpc";

// Helper to format numbers with 2 decimals (display like payroll modal)
function formatAmount(amount) {
    if (amount === undefined || amount === null || isNaN(amount)) {
        return "0.00";
    }
    return (Math.round(Number(amount) * 100) / 100).toFixed(2);
}

SalaryPackageWidget.include({
    async updateGrossToNetModal(data) {
        // Build modal content from offer structure lines instead of payroll payslip
        const offerId = parseInt(document.querySelector("input[name='offer_id']")?.value);
        let linesPayload = [];

        try {
            if (offerId) {
                const response = await rpc('/salary_package/offer_lines', { offer_id: offerId });
                const datas = response?.datas || [];
                for (const item of datas) {
                    // item = (label, valueNumeric, code, sign, position, symbol)
                    const valueText = formatAmount(item[1]);
                    linesPayload.push([
                        item[0],           // label
                        valueText,         // value text for position 'after'
                        item[2],           // code
                        item[3],           // sign
                        item[4],           // currency position
                        item[5],           // currency symbol
                    ]);
                }
            }
        } catch (e) {
            // Fallback to empty payload on error
            console.error('Error while fetching offer structure lines', e);
        }

        const modalBody = renderToElement('salary_config.offer_structure_modal', { datas: linesPayload });
        this.$("main.modal-body").html(modalBody);
        // Reproduce the base behavior for resume sidebar and NET updates
        try {
            const resumeSidebar = renderToElement('hr_contract_salary.salary_package_resume', {
                'lines': data.resume_lines_mapped,
                'categories': data.resume_categories,
                'configurator_warning': data.configurator_warning,
            });
            this.$("div[name='salary_package_resume']").html(resumeSidebar);
            $("input[name='wage_with_holidays']").val(data['wage_with_holidays']);
            $("div[name='net']").removeClass('d-none').hide().slideDown("slow");
            $("input[name='NET']").removeClass('o_outdated');
        } catch (e) {
            // As a safety net, if the base template isn't available, just ignore
            console.warn('Resume sidebar update skipped:', e);
        }
        // Avoid calling super to prevent null _super.apply issues
        return;
    },
});
