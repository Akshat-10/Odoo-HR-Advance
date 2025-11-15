# Bugfix v1.4.1 - Amount Rounding Implementation Fix

## Issue Description
Version 1.4.0 attempted to implement amount rounding by overriding `_compute_total()` in `hr.payslip.line` model. However, this approach didn't work because:

1. **`total` is NOT a computed field** - The `total` field in `hr.payslip.line` is a simple `fields.Monetary()` field (not a `fields.Monetary(compute='...')`)
2. **Values are written directly** - During payslip computation, the `total` value is calculated and **written directly** to the database via `_get_payslip_line_total()` method in `hr.payslip`
3. **`_compute_total()` never triggers** - Since `total` is not a computed field, adding `@api.depends` decorators on a non-computed field has no effect

## Root Cause Analysis

### Incorrect Approach (v1.4.0)
```python
# models/hr_payslip_line.py - THIS DOESN'T WORK
class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        # This method is NEVER called because 'total' is not a computed field
        pass
```

### How Payslip Line Total Actually Works

In base Odoo (`hr_payroll`):
1. `hr.payslip._get_payslip_lines()` calls salary rule computation
2. For each rule, `_get_payslip_line_total(amount, quantity, rate, rule)` calculates: `amount * quantity * rate / 100.0`
3. This calculated value is **directly written** to the `total` field when creating/updating payslip lines

```python
# PAYroll-modules-ent/hr_payroll/models/hr_payslip.py line 837
def _get_payslip_line_total(self, amount, quantity, rate, rule):
    self.ensure_one()
    return amount * quantity * rate / 100.0  # ← This value is used directly
```

## Solution (v1.4.1)

Override `_get_payslip_line_total()` in `hr.payslip` model to apply rounding **at the source**:

```python
# models/hr_payslip.py
def _get_payslip_line_total(self, amount, quantity, rate, rule):
    """Override to round line total to whole numbers"""
    total = super()._get_payslip_line_total(amount, quantity, rate, rule)
    return self._round_to_whole(total)
```

This approach:
✅ Intercepts total calculation at the correct point
✅ Rounds values before they're written to the database
✅ Works for ALL payslip lines (Basic, Gross, Net, Allowances, Deductions)
✅ Consistent with `_get_paid_amount()` override already in place

## Changes Made

### Files Modified
1. **models/hr_payslip.py**
   - Added `_get_payslip_line_total()` override with rounding

### Files Removed
1. **models/hr_payslip_line.py**
   - Removed - incorrect approach that never executed

2. **models/__init__.py**
   - Removed `hr_payslip_line` import

### Version Updated
- `__manifest__.py` version bumped to **1.4.1**

## Testing Verification

After upgrading to v1.4.1, verify rounding works:

1. Create a new payslip or recompute existing one
2. Check `Worked Days & Inputs` tab - amounts should be whole numbers
3. Check payslip lines (Basic, Gross, Net, etc.) - all `Total` values should have no decimals
4. Check `paid_amount` property - should be rounded

### Expected Results
| Before (v1.4.0) | After (v1.4.1) |
|-----------------|----------------|
| 32424.43 | 32424.00 |
| 32424.67 | 32425.00 |
| 4423.54 | 4424.00 |
| -1234.67 | -1235.00 |

## Upgrade Instructions

```powershell
cd C:\odoo\odoo_v18\odoo18
.\odoo-bin -c ..\odoo_v18.conf -d <your_database> -u hr_payroll_workdays_extended --stop-after-init
```

After upgrade:
1. Open any payslip in "Draft" state
2. Click "Compute Sheet" to recalculate
3. Verify all amounts are rounded to whole numbers
4. If payslip is already computed, click "Cancel" → "Compute Sheet" again

## Technical Notes

### Why This Matters
- **Data Consistency**: All amount calculations now happen at the source method
- **Maintainability**: Single point of rounding for all payslip calculations
- **Performance**: No additional compute triggers - rounding happens during normal flow
- **Compatibility**: Works with all salary rules (Python code, percentage, fixed amount)

### Rounding Logic
Uses `math.floor(x + 0.5)` for positive and `math.ceil(x - 0.5)` for negative numbers:
- **0.5 and above** → rounds UP
- **Below 0.5** → rounds DOWN
- Works correctly for negative amounts (e.g., deductions)

---

**Date**: 2025-01-XX  
**Issue**: Amount rounding not working (v1.4.0)  
**Fix**: Override correct method (_get_payslip_line_total)  
**Version**: 1.4.1
