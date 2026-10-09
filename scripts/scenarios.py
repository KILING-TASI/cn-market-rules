"""Offline, explicitly parameterized research arithmetic. No market/account access."""
from __future__ import annotations

import argparse
import json
import operator
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

D = Decimal
ZERO = D('0')

def num(obj, key, minimum=None, maximum=None):
    if key not in obj or isinstance(obj[key], bool) or obj[key] is None:
        raise ValueError(f'{key}: required numeric value')
    try:
        value = D(str(obj[key]))
    except (InvalidOperation, ValueError):
        raise ValueError(f'{key}: invalid numeric value') from None
    if not value.is_finite():
        raise ValueError(f'{key}: must be finite')
    if minimum is not None and value < D(str(minimum)):
        raise ValueError(f'{key}: below minimum {minimum}')
    if maximum is not None and value > D(str(maximum)):
        raise ValueError(f'{key}: above maximum {maximum}')
    return value

def integer(obj, key, minimum=0):
    value = num(obj, key, minimum)
    if value != value.to_integral_value():
        raise ValueError(f'{key}: integer required')
    return int(value)

def flag(obj, key):
    if type(obj.get(key)) is not bool:
        raise ValueError(f'{key}: explicit boolean required; unknown is not false')
    return obj[key]

def label(obj, key):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{key}: nonempty text required')
    return value.strip()

def iso(obj, key):
    try:
        return date.fromisoformat(label(obj, key))
    except ValueError:
        raise ValueError(f'{key}: ISO date required') from None

def money(value):
    return str(value.quantize(D('.01'), rounding=ROUND_HALF_UP))

def ratio(value):
    return str(value.quantize(D('.000001'), rounding=ROUND_HALF_UP))

def carrying(obj, capital):
    return capital * num(obj, 'annual_opportunity_rate', 0, 1) * integer(obj, 'holding_days') / 365

def dilution(obj):
    principal = D(integer(obj, 'outstanding_principal', 1))
    old_price = num(obj, 'old_conversion_price', '.000001')
    new_price = num(obj, 'new_conversion_price', '.000001')
    if new_price >= old_price:
        raise ValueError('new_conversion_price must be below old_conversion_price')
    existing = D(integer(obj, 'existing_shares', 1))
    profit = num(obj, 'net_profit_ttm')
    underlying = num(obj, 'underlying_price', '.000001')
    fraction = num(obj, 'conversion_fraction', 0, 1)
    old_new_shares = principal * fraction / old_price
    new_new_shares = principal * fraction / new_price
    old_dilution = old_new_shares / (existing + old_new_shares)
    new_dilution = new_new_shares / (existing + new_new_shares)
    eps_current = profit / existing
    eps_old = profit / (existing + old_new_shares)
    eps_new = profit / (existing + new_new_shares)
    compression = (1 - eps_new / eps_old) if profit > 0 else None
    loss_change = (1 - abs(eps_new) / abs(eps_old)) if profit < 0 else None
    adjusted_eps = None
    if 'profit_adjustment' in obj:
        adjusted_eps = ratio((profit + num(obj, 'profit_adjustment')) / (existing + new_new_shares))
    return {
        'mode': 'dilution', 'conversion_fraction': ratio(fraction),
        'theoretical_new_shares_old_price': ratio(old_new_shares),
        'theoretical_new_shares_new_price': ratio(new_new_shares),
        'additional_shares_due_to_revision': ratio(new_new_shares - old_new_shares),
        'dilution_ratio_old_price': ratio(old_dilution),
        'dilution_ratio_new_price': ratio(new_dilution),
        'additional_dilution_ratio': ratio(new_dilution - old_dilution),
        'conversion_value_old_per_100': money(100 * underlying / old_price),
        'conversion_value_new_per_100': money(100 * underlying / new_price),
        'conversion_value_uplift_ratio': ratio(old_price / new_price - 1),
        'static_eps_current': ratio(eps_current), 'static_eps_old_price': ratio(eps_old),
        'static_eps_new_price': ratio(eps_new),
        'positive_profit_eps_compression_ratio': None if compression is None else ratio(compression),
        'loss_per_share_absolute_reduction_ratio': None if loss_change is None else ratio(loss_change),
        'adjusted_eps_new_price': adjusted_eps,
        'profit_interpretation': 'positive' if profit > 0 else ('loss: less negative per-share arithmetic is not operating improvement' if profit < 0 else 'zero profit: EPS ratios undefined'),
        'legal_floor_check': 'not assessed; verify statutory and individual bond price constraints',
        'dilution_is_not_loss': 'ownership dilution is not shareholder economic loss',
        'assumptions': 'same-date remaining principal/current shares including previous conversions; same conversion fraction; constant profit and reference price; theoretical fractional shares; no accounting weighted-average EPS'
    }

def tender(obj):
    qty = integer(obj, 'quantity', 1)
    cost = num(obj, 'buy_price', '.000001')
    offer = num(obj, 'offer_price', 0)
    fraction = num(obj, 'accepted_ratio', 0, 1)
    residual = num(obj, 'residual_exit_price', 0)
    fees = num(obj, 'total_fees', 0)
    initial = qty * cost
    carry = carrying(obj, initial)
    proceeds = qty * (fraction * offer + (1 - fraction) * residual)
    pnl = proceeds - initial - fees - carry
    break_even = None if fraction == 1 else (initial + fees + carry - qty * fraction * offer) / (qty * (1 - fraction))
    return {'mode': 'tender', 'gross_proceeds': money(proceeds), 'opportunity_cost': money(carry),
            'net_pnl': money(pnl), 'return_on_cost': ratio(pnl / initial),
            'break_even_residual_price': None if break_even is None else ratio(break_even),
            'qualification': 'not assessed; accepted_ratio is an explicit scenario input'}

def merger(obj):
    qty = integer(obj, 'quantity', 1)
    initial = qty * num(obj, 'buy_price', '.000001')
    exchange_ratio = num(obj, 'exchange_ratio', '.000001')
    credited_shares = integer(obj, 'actual_converted_shares')
    price = num(obj, 'survivor_exit_price', 0)
    tail = num(obj, 'tail_cash_adjustment', 0)
    fees = num(obj, 'total_fees', 0)
    carry = carrying(obj, initial)
    pnl = credited_shares * price + tail - initial - fees - carry
    return {'mode': 'merger', 'theoretical_shares': ratio(qty * exchange_ratio),
            'actual_converted_shares': credited_shares,
            'reference_value_per_original_share': ratio(exchange_ratio * price),
            'net_pnl': money(pnl), 'return_on_cost': ratio(pnl / initial),
            'fractional_share_handling': 'proceeds use explicit actual credited shares plus verified tail cash, not fractional theoretical shares'}

def exit_scenario(obj):
    initial = num(obj, 'invested_cost', '.000001')
    cash = num(obj, 'exit_cash', 0)
    residual = num(obj, 'residual_asset_value', 0)
    fees = num(obj, 'total_fees', 0)
    carry = carrying(obj, initial)
    pnl = cash + residual - initial - fees - carry
    return {'mode': 'exit', 'net_pnl': money(pnl), 'return_on_cost': ratio(pnl / initial),
            'cash_received': money(cash), 'residual_value_is_not_cash': money(residual),
            'opportunity_cost': money(carry), 'legal_eligibility': 'not assessed'}

def reits(obj):
    if label(obj, 'market') != 'SSE' or label(obj, 'offering_type') != 'initial':
        raise ValueError('reits: only SSE initial offering is supported')
    registered = num(obj, 'registered_units', 1)
    final = num(obj, 'final_units', 0, registered)
    strategic = num(obj, 'strategic_units', 0, final)
    offline = num(obj, 'offline_units', 0, final - strategic)
    funds = num(obj, 'raised_funds', 0)
    investors = integer(obj, 'investors')
    compliance = flag(obj, 'originator_compliant')
    other = flag(obj, 'other_failure_condition')
    public_pool = final - strategic
    if public_pool <= 0:
        raise ValueError('reits: nonstrategic denominator must be positive')
    fraction = offline / public_pool
    checks = {'units_below_80_percent': final < registered * D('.80'),
              'funds_below_200m_or_investors_below_1000': funds < 200_000_000 or investors < 1000,
              'originator_noncompliance': not compliance,
              'offline_below_70_percent_of_nonstrategic': fraction < D('.70'),
              'other_failure_condition': other}
    return {'mode': 'reits', 'nonstrategic_denominator_units': str(public_pool),
            'offline_ratio': ratio(fraction), 'minimum_offline_units': str(public_pool * D('.70')),
            'failure_checks': checks, 'failure_condition_detected': any(checks.values()),
            'status': 'arithmetic conditions only; formal offering result requires manager announcement'}

def reits_return(obj):
    subscription = num(obj, 'subscription_amount', '.000001')
    price = num(obj, 'offering_price', '.000001')
    allocation = num(obj, 'allocation_ratio', 0, 1)
    exit_price = num(obj, 'exit_price', 0)
    distributions = num(obj, 'cash_distributions', 0)
    fees = num(obj, 'total_fees', 0)
    # Explicit yuan-days accounts for full subscription before refund, then allocation.
    yuan_days = num(obj, 'capital_days', 0)
    carry = yuan_days * num(obj, 'annual_opportunity_rate', 0, 1) / 365
    units = subscription / price * allocation
    allocated_cost = units * price
    pnl = units * (exit_price - price) + distributions - fees - carry
    return {'mode': 'reits_return', 'theoretical_allocated_units': ratio(units),
            'allocated_cost': money(allocated_cost), 'unallocated_refund_principal': money(subscription - allocated_cost),
            'opportunity_cost': money(carry), 'net_pnl': money(pnl),
            'return_on_subscription': ratio(pnl / subscription),
            'return_on_allocated_cost': None if allocated_cost == 0 else ratio(pnl / allocated_cost),
            'rounding': 'actual unit confirmation and subscription fees must replace theoretical allocation'}

def repo(obj):
    trade = iso(obj, 'trade_date')
    start, end = iso(obj, 'calendar_start'), iso(obj, 'calendar_end')
    calendar_source = label(obj, 'calendar_source')
    if not start <= trade <= end:
        raise ValueError('trade date outside declared calendar coverage')
    raw_days = obj.get('trading_days')
    if not isinstance(raw_days, list) or not raw_days:
        raise ValueError('trading_days: explicit complete calendar required')
    try:
        days = [date.fromisoformat(x) for x in raw_days]
    except (ValueError, TypeError):
        raise ValueError('trading_days: invalid ISO date') from None
    if days != sorted(set(days)) or any(d < start or d > end for d in days):
        raise ValueError('trading_days: unique ascending days within coverage required')
    if trade not in days:
        raise ValueError('trade_date must be in trading_days')
    tenor = integer(obj, 'tenor_days', 1)
    if tenor not in {1, 2, 3, 4, 7, 14, 28, 91, 182}:
        raise ValueError('unsupported repo tenor')
    def next_day(after, inclusive=False):
        found = [d for d in days if d >= after] if inclusive else [d for d in days if d > after]
        if not found:
            raise ValueError('calendar coverage insufficient; no extrapolation allowed')
        return found[0]
    first = next_day(trade)
    nominal = trade + timedelta(days=tenor)
    if nominal > end:
        raise ValueError('nominal maturity outside calendar coverage')
    clearing = next_day(nominal, True)
    final = next_day(clearing)
    interest_days = (final - first).days
    principal = num(obj, 'principal', 1000)
    if principal % 1000:
        raise ValueError('repo matched trading principal must be a multiple of 1000')
    annual_rate = num(obj, 'annual_rate', 0, 1)
    fees = num(obj, 'total_fees', 0)
    interest = principal * annual_rate * interest_days / 365
    return {'mode': 'repo', 'first_settlement_date': first.isoformat(),
            'nominal_maturity_date': nominal.isoformat(), 'maturity_clearing_date': clearing.isoformat(),
            'funds_available_date': clearing.isoformat(), 'final_settlement_date': final.isoformat(),
            'funds_withdrawable_date': final.isoformat(), 'interest_days': interest_days,
            'gross_interest': money(interest), 'net_interest': money(interest - fees),
            'calendar_source': calendar_source, 'assumption': 'normal settlement; broker availability must be confirmed'}

def cash(obj):
    balance = num(obj, 'initial_available_cash', 0)
    initial = balance
    buffer = num(obj, 'minimum_buffer', 0)
    events = obj.get('events')
    if not isinstance(events, list):
        raise ValueError('events: list required')
    ordered = []
    for event in events:
        if not isinstance(event, dict):
            raise ValueError('cash event must be object')
        try:
            stamp = datetime.fromisoformat(label(event, 'at'))
        except ValueError:
            raise ValueError('event at: ISO datetime required') from None
        if stamp.tzinfo is not None:
            raise ValueError('use local naive timestamps in one explicit timezone')
        name, source = label(event, 'name'), label(event, 'source')
        amount = num(event, 'amount')
        if label(event, 'cash_state') != 'available':
            raise ValueError('cash: include available cash only; pending refunds/asset values are not cash')
        ordered.append((stamp, amount >= 0, name, amount, source))
    label(obj, 'timezone')
    ordered.sort(key=lambda row: (row[0], row[1], row[2]))
    low = balance
    trajectory = []
    for stamp, _, name, amount, source in ordered:
        balance += amount
        low = min(low, balance)
        trajectory.append({'at': stamp.isoformat(), 'name': name, 'amount': money(amount),
                           'balance': money(balance), 'buffer_gap': money(max(ZERO, buffer - balance)), 'source': source})
    return {'mode': 'cash', 'initial_cash': money(initial), 'final_cash': money(balance),
            'minimum_balance': money(low), 'maximum_cash_shortfall': money(max(ZERO, -low)),
            'maximum_buffer_gap': money(max(ZERO, buffer - low)), 'trajectory': trajectory}

def clause(obj):
    window = integer(obj, 'window', 1)
    required = integer(obj, 'required_hits', 1)
    if required > window:
        raise ValueError('required_hits cannot exceed window')
    threshold = num(obj, 'threshold', '.000001')
    comparison = label(obj, 'comparison')
    compare = {'lt': operator.lt, 'le': operator.le, 'gt': operator.gt, 'ge': operator.ge}.get(comparison)
    if compare is None:
        raise ValueError('comparison must be lt/le/gt/ge')
    lists = [obj.get(k) for k in ('dates', 'prices', 'conversion_prices')]
    if any(not isinstance(xs, list) for xs in lists) or not lists[0] or len({len(xs) for xs in lists}) != 1:
        raise ValueError('dates/prices/conversion_prices must be nonempty equal-length lists')
    dates, prices, conversions = lists
    try:
        parsed_dates = [date.fromisoformat(x) for x in dates]
    except (ValueError, TypeError):
        raise ValueError('dates: ISO date required') from None
    if parsed_dates != sorted(set(parsed_dates)):
        raise ValueError('dates must be unique ascending')
    hits = [compare(num({'p': p}, 'p', '.000001'), num({'c': c}, 'c', '.000001') * threshold)
            for p, c in zip(prices, conversions)]
    count = sum(hits[-window:])
    consecutive = 0
    for hit in reversed(hits):
        if not hit:
            break
        consecutive += 1
    return {'mode': 'clause', 'window_observed': min(len(hits), window), 'window_hits': count,
            'hits_remaining_in_current_window': max(0, required - count), 'trailing_consecutive_hits': consecutive,
            'required_hits_reached': count >= required,
            'window_complete': len(hits) >= window,
            'calendar_and_contract': 'input sequence must contain all eligible days; legal trigger not independently assessed'}

MODES = {'dilution': dilution, 'tender': tender, 'merger': merger, 'exit': exit_scenario, 'reits': reits,
         'reits_return': reits_return, 'repo': repo, 'cash': cash, 'clause': clause}

def calculate(obj):
    if not isinstance(obj, dict):
        raise ValueError('case must be an object')
    mode = label(obj, 'mode')
    if mode not in MODES:
        raise ValueError(f'unknown mode: {mode}')
    result = MODES[mode](obj)
    if 'name' in obj:
        result['name'] = label(obj, 'name')
    return result

def run(document):
    if isinstance(document, dict) and 'cases' in document:
        if not isinstance(document['cases'], list) or not document['cases']:
            raise ValueError('cases: nonempty list required')
        return {'results': [calculate(case) for case in document['cases']],
                'notice': 'scenario arithmetic; no live data, eligibility decision or execution'}
    return calculate(document)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.input.read_text(encoding='utf-8-sig'), parse_float=D)
        output = json.dumps(run(document), ensure_ascii=False, indent=2)
    except (ValueError, OSError, InvalidOperation, KeyError, TypeError) as error:
        parser.exit(2, f'Input/calculation error: {error}\n')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + '\n', encoding='utf-8')
    else:
        print(output)

if __name__ == '__main__':
    main()
