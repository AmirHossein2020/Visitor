def gregorian_to_jalali(year, month, day):
    g_days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    year -= 1600
    month -= 1
    day -= 1
    days = 365 * year + (year + 3) // 4 - (year + 99) // 100 + (year + 399) // 400
    days += sum(g_days[:month]) + day
    if month > 1 and ((year + 1600) % 4 == 0 and ((year + 1600) % 100 != 0 or (year + 1600) % 400 == 0)):
        days += 1
    days -= 79
    cycle, days = divmod(days, 12053)
    jy = 979 + cycle * 33 + 4 * (days // 1461)
    days %= 1461
    if days >= 366:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def format_jalali_datetime(value):
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d} - {value:%H:%M}"
