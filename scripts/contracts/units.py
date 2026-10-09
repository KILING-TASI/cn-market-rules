"""Describe native units without converting values or changing scale."""
UNITS={
    'ratio':('fraction',None,'1'),
    'shares':('share_count',None,'1'),
    'units':('fund_unit_count',None,'1'),
    'CNY':('money','CNY','1'),
    'CNY/share':('money_per_share','CNY','1'),
    'CNY/unit':('money_per_fund_unit','CNY','1'),
    'date':('calendar_date',None,None),
    'timestamp':('timestamp',None,None),
}

def unit_view(fact):
    native=fact['unit'];family,currency,scale=UNITS.get(native,('unmapped',None,None))
    return dict(key=fact['key'],native_unit=native,unit_family=family,currency=currency,scale=scale,conversion='none; value retained verbatim')
