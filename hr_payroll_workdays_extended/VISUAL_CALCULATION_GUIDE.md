# Week-Off Hours Calculation - Visual Flow Diagram

## 📊 Calculation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     PAYSLIP PERIOD                              │
│                   (e.g., Jan 1-31, 2025)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │   Read Employee's Working Schedule     │
         │     (resource.calendar)                │
         └────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
    ┌──────────────────────┐   ┌──────────────────────┐
    │  Working Days        │   │  Week-Off Days       │
    │  (Mon-Fri)           │   │  (Sat-Sun)           │
    │  = 22 days           │   │  = 8 days            │
    │  × 8 hrs = 176 hrs   │   │  × 8 hrs = 64 hrs    │
    └──────────────────────┘   └──────────────────────┘
                │                           │
                └─────────────┬─────────────┘
                              ▼
                ┌──────────────────────────┐
                │   TOTAL PERIOD HOURS     │
                │   176 + 64 = 240 hours   │
                └──────────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │        HOURLY RATE CALCULATION           │
         │                                          │
         │  Monthly Wage / Total Period Hours       │
         │  $3,000 / 240 = $12.50/hour             │
         └─────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
    ┌──────────────────────┐   ┌──────────────────────┐
    │  Working Days Pay    │   │  Week-Off Days Pay   │
    │  176 hrs × $12.50    │   │  64 hrs × $0.00      │
    │  = $2,200.00 ✓       │   │  = $0.00 ✗           │
    └──────────────────────┘   └──────────────────────┘
                │                           │
                └─────────────┬─────────────┘
                              ▼
                ┌──────────────────────────┐
                │    TOTAL PAYSLIP PAY     │
                │       $2,200.00          │
                └──────────────────────────┘
```

## 📈 Comparison: Old vs New

### OLD CALCULATION (v1.1.0)
```
Monthly Wage: $3,000
Working Hours: 176

Hourly Rate = $3,000 / 176 = $17.05/hour

Payslip:
  Attendance: 176 hrs × $17.05 = $3,000.00 ✓
  Week-Off: Not shown
  ────────────────────────────────────────
  TOTAL: $3,000.00 (Full monthly wage)
```

### NEW CALCULATION (v1.2.0)
```
Monthly Wage: $3,000
Working Hours: 176
Week-Off Hours: 64
Total Hours: 240

Hourly Rate = $3,000 / 240 = $12.50/hour

Payslip:
  Attendance: 176 hrs × $12.50 = $2,200.00 ✓ PAID
  Week-Off:    64 hrs × $0.00  =     $0.00 ✗ NOT PAID
  ────────────────────────────────────────────────
  TOTAL: $2,200.00 (Proportional to days worked)
```

## 🎯 Key Differences

| Aspect | Old (v1.1.0) | New (v1.2.0) |
|--------|--------------|--------------|
| **Divisor** | Working hours only | Working + Week-off hours |
| **Hourly Rate** | Higher ($17.05) | Lower ($12.50) |
| **Week-offs** | Not shown | Shown as $0.00 |
| **Total Pay** | Full wage ($3,000) | Proportional ($2,200) |
| **Use Case** | Fixed monthly pay | Attendance-based pay |

## 💡 Why This Makes Sense

### Customer's Requirement:
"Include week-off days hours in the total hours for hourly wage calculation"

### Result:
✅ **Lower hourly rate** - Because total hours includes unpaid week-offs  
✅ **Proportional pay** - Employees paid only for days worked  
✅ **Transparent tracking** - Week-offs visible but marked as unpaid  
✅ **Fair calculation** - Rate reflects full period, not just working days

## 📋 Working Schedule Impact

### Example 1: 5-Day Work Week (Mon-Fri)
```
Working Days per Week: 5
Week-Off Days per Week: 2

Monthly (31 days):
  Working: 22 days (176 hrs)
  Week-off: 8 days (64 hrs)
  Rate: Lower due to week-offs
```

### Example 2: 6-Day Work Week (Mon-Sat)
```
Working Days per Week: 6
Week-Off Days per Week: 1

Monthly (31 days):
  Working: 26 days (208 hrs)
  Week-off: 4 days (32 hrs)
  Rate: Higher than 5-day week (fewer week-offs)
```

### Example 3: 7-Day Work Week (No Week-offs)
```
Working Days per Week: 7
Week-Off Days per Week: 0

Monthly (31 days):
  Working: 31 days (248 hrs)
  Week-off: 0 days (0 hrs)
  Rate: Highest (no week-offs diluting rate)
```

## 🔄 Period Hours Breakdown

```
┌────────────────────────────────────────────────────┐
│                JANUARY 2025 (31 Days)              │
├────────────────────────────────────────────────────┤
│                                                    │
│  SUN  MON  TUE  WED  THU  FRI  SAT                │
│  [W]  [✓]  [✓]  [✓]  [✓]  [✓]  [W]   Week 1      │
│  [W]  [✓]  [✓]  [✓]  [✓]  [✓]  [W]   Week 2      │
│  [W]  [✓]  [✓]  [✓]  [✓]  [✓]  [W]   Week 3      │
│  [W]  [✓]  [✓]  [✓]  [✓]  [✓]  [W]   Week 4      │
│  [W]  [✓]  [✓]                        Week 5      │
│                                                    │
│  Legend:                                           │
│  [✓] = Working Day (8 hours)                      │
│  [W] = Week-Off Day (8 hours, unpaid)            │
│                                                    │
│  Working Days: 22 days × 8 hrs = 176 hrs         │
│  Week-Off Days: 8 days × 8 hrs = 64 hrs          │
│  Total Period: 31 days, 240 hours                 │
│                                                    │
│  Hourly Rate: $3,000 / 240 = $12.50/hour         │
│  Pay: 176 hrs × $12.50 = $2,200.00               │
│                                                    │
└────────────────────────────────────────────────────┘
```

## 🎓 Understanding the Math

### Step-by-Step Calculation:

**Step 1: Count Days**
```
Total Days in Period: 31
Working Days (Mon-Fri): 22
Week-Off Days (Sat-Sun): 8
Public Holidays: 1
Check: 22 + 8 + 1 = 31 ✓
```

**Step 2: Calculate Hours**
```
Hours Per Day: 8
Working Hours: 22 × 8 = 176
Week-Off Hours: 8 × 8 = 64
Total Period Hours: 176 + 64 = 240
```

**Step 3: Calculate Hourly Rate**
```
Monthly Wage: $3,000
Total Period Hours: 240
Hourly Rate: $3,000 ÷ 240 = $12.50/hour
```

**Step 4: Calculate Pay**
```
Working Days: 176 hrs × $12.50 = $2,200.00 ✓ PAID
Week-Off Days: 64 hrs × $0.00 = $0.00 ✗ NOT PAID
Total Pay: $2,200.00
```

## 📊 Impact on Different Scenarios

### Scenario 1: Full Month Worked
```
Working Days: 22/22 (100%)
Pay: $2,200 (100% of proportional wage)
```

### Scenario 2: 2 Days Leave
```
Working Days: 20/22 (91%)
Leave Days: 2 (paid)
Week-Off Days: 8 (unpaid)
Pay: (20 + 2) × 8 × $12.50 = $2,200
```

### Scenario 3: 2 Days Absent (Unpaid)
```
Working Days: 20/22 (91%)
Absent Days: 2 (unpaid)
Week-Off Days: 8 (unpaid)
Pay: 20 × 8 × $12.50 = $2,000
```

---
**Visual Guide Version**: 1.2.0  
**Created**: November 2025
