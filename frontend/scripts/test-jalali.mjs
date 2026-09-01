import assert from "node:assert/strict";
import {daysInJalaliMonth,gregorianToJalali,jalaliMonthRange,jalaliToGregorian} from "../src/services/jalali.js";
assert.deepEqual(gregorianToJalali("2026-09-01"),{year:1405,month:6,day:10});
assert.equal(jalaliToGregorian(1403,1,1),"2024-03-20");
assert.equal(jalaliToGregorian(1404,1,1),"2025-03-21");
assert.equal(daysInJalaliMonth(1399,12),30);
assert.equal(daysInJalaliMonth(1400,12),29);
assert.deepEqual(jalaliMonthRange(1405,6),{from:"2026-08-23",to:"2026-09-22"});
console.log("Jalali conversion tests passed.");
