# SPDX-License-Identifier: MIT
"""Versioned research checks; disclosed subsets never become institutional compliance certification."""
from datetime import date,timedelta
from decimal import Decimal
from review_io import day,number,cli
TAX='https://shanghai.chinatax.gov.cn/zcfw/zcfgk/grsds/201509/t418999.html'
CALENDAR='https://shanghai.chinatax.gov.cn/zcfw/zcjd/201509/t419000.html'
OPERATIONS='https://www.csrc.gov.cn/csrc/c106256/c1653978/content.shtml'
LIQUIDITY='https://www.csrc.gov.cn/csrc/c101877/c1029552/content.shtml'

def positive(x):
    n=number(x)
    if n<=0:raise ValueError('分母须大于零')
    return n

def nonnegative(x):
    n=number(x)
    if n<0:raise ValueError('数量/金额不得负')
    return n

def anniversary(start,months):
    year=start.year+(start.month-1+months)//12;month=(start.month-1+months)%12+1
    try:return date(year,month,start.day)
    except ValueError:return None  # Month-end/leap-date handling requires settlement evidence, not a guessed roll rule.

def dividend_tax(spec):
    if spec.get('investorType')!='individual' or spec.get('instrument')!='direct-listed-A-share' or spec.get('market') not in {'SSE','SZSE'} or spec.get('restricted') is not False:raise ValueError('首版只处理沪深个人直接持有非限售A股，不套基金/REITs/机构/其他市场')
    record=day(spec['recordDate']);transfer=day(spec['transferSettlementDate'])
    if record<=date(2015,9,8) or transfer<=record:raise ValueError('需2015政策适用登记日及登记后明确转让交割日')
    qty=positive(spec['soldDividendEntitledShares']);per=nonnegative(spec['grossDividendPerShare']);lots=spec['lots'];dates=[day(r['acquiredDate']) for r in lots]
    if dates!=sorted(dates) or any(d>record for d in dates):raise ValueError('分批持仓须按取得顺序且不晚于登记日')
    available=sum((nonnegative(r['remainingDividendEntitledShares']) for r in lots),Decimal(0))
    if qty>available:raise ValueError('转让分红权益股数超出所填留存批次')
    remaining=qty;rows=[];tax=Decimal(0);unknown=False
    for row,start in zip(lots,dates):
        quantity=min(remaining,nonnegative(row['remainingDividendEntitledShares']));remaining-=quantity
        if quantity==0:continue
        month,year=anniversary(start,1),anniversary(start,12)
        rate=None if month is None or year is None else Decimal('.2') if transfer<=month else Decimal('.1') if transfer<=year else Decimal(0)
        unknown|=rate is None
        due=None if rate is None else quantity*per*rate
        if due is not None:tax+=due
        rows.append({'acquiredDate':row['acquiredDate'],'holdingEndDate':(transfer-timedelta(days=1)).isoformat(),'allocatedShares':str(quantity),'rate':None if rate is None else str(rate),'estimatedTax':None if due is None else str(due)})
    return {'rulesVersion':'personal-direct-SSE-SZSE-dividend-2015-101-and-calendar-1','conclusion':'按留存批次先进先出和交割日前一天核对持有期限；这是声明权益股份的税款情景，不是券商实际扣税账单。','lots':rows,'estimatedTax':None if unknown else str(tax),'grossDividendOnSoldShares':str(qty*per),'humanRows':[['卖出权益股数',str(qty)],['税款情景（元）','未知：月底/闰日界限需登记口径' if unknown else str(tax)]],'sources':[TAX,CALENDAR],'limitations':['所填批次须已扣除此前转让、登记权益变化；首版不重建完整账户流水','同日多批次以输入留存顺序核对，不自动证明结算先后','自然月/年不是30/365天；月底及闰日无同日周年时保留未知','不套用已废止第四条，不计算基金及REIT分配税，也不构成纳税认证']}

PROFILES={
 'single-fund-issuer':('net-assets',Decimal('.10'),OPERATIONS,'§32(1)'),
 'manager-all-funds-security':('issued-security-units',Decimal('.10'),OPERATIONS,'§32(2)'),
 'fof-single-fund':('net-assets',Decimal('.20'),OPERATIONS,'§32(5)'),
 'open-fund-restricted':('net-assets',Decimal('.15'),LIQUIDITY,'§16'),
 'money-fund-restricted':('net-assets',Decimal('.10'),LIQUIDITY,'§32'),
 'manager-open-funds-free-float':('free-float-shares',Decimal('.15'),LIQUIDITY,'§15'),
 'manager-all-portfolios-free-float':('free-float-shares',Decimal('.30'),LIQUIDITY,'§15')}

def limits(spec):
    day(spec['asOf']);out=[];ids=set()
    for row in spec['checks']:
        if not row.get('id') or row['id'] in ids or row.get('profile') not in PROFILES:raise ValueError('限额核对需唯一ID及支持的规则类型')
        ids.add(row['id']);basis,limit,url,clause=PROFILES[row['profile']]
        if row.get('denominatorBasis')!=basis:raise ValueError('限额分母错误，净资产/发行量/可流通股不可互换')
        scope=row.get('scope');applicable=row.get('applicable');exemption=row.get('exemptionStatus');passive=row.get('passiveBreach')
        if scope not in {'complete-declared','partial'} or applicable not in (True,False,None) or exemption not in {'none-declared','claimed','unknown'} or not isinstance(passive,bool):raise ValueError('需明确范围、适用/例外状态和主动被动变化')
        numerator=nonnegative(row['numerator']);denominator=positive(row['denominator']);ratio=numerator/denominator
        if applicable is False:status='not-applicable-declared'
        elif applicable is not True or exemption!='none-declared':status='applicability-or-exception-review-needed'
        elif ratio>limit:status='observed-above-threshold-review-needed'
        elif scope=='partial':status='unknown-full-scope'
        else:status='within-declared-numeric-threshold'
        out.append({'id':row['id'],'profile':row['profile'],'ratio':str(ratio),'threshold':str(limit),'denominatorBasis':basis,'status':status,'passiveBreach':passive,'source':url,'clause':clause,'ruleSelection':'explicit-2014-operations-or-2017-liquidity; not-automatically-latest-applicability','nextStep':'核产品类型、基金合同、特殊豁免、成立期及被动超限处理；不自行认定违规。'})
    return {'rulesVersion':'selected-fund-limits-research-1','conclusion':'分别核对分母、机构范围和例外；数值位于线内不等于整只基金或管理人已合规。','checks':out,'humanRows':[[r['id'],r['status']+'；比例'+r['ratio']] for r in out],'limitations':['规则版本显式限定2014运作及2017流动性条款，使用前需核最新修订和产品适用','不推断指数复制、特殊品种、定开开放期或货币基金例外；未核则未知','管理人范围不能用单只基金或十大持仓代替；成立期和被动变化处理另核']}

def redemption_liquidity(spec):
    if spec.get('product')!='open-fund' or spec.get('specialException') not in {'none-declared','unknown','claimed'}:raise ValueError('需明确开放式基金及特殊例外状态')
    day(spec['asOf']);liquid=nonnegative(spec['declaredSevenWorkdayRealizableValue']);redemption=nonnegative(spec['confirmedNetRedemption'])
    if spec.get('coverage') not in {'complete-declared','partial'}:raise ValueError('需完整/部分声明范围')
    status='review-applicability' if spec['specialException']!='none-declared' else 'observed-cash-gap' if redemption>liquid else 'within-declared-value' if spec['coverage']=='complete-declared' else 'unknown-full-scope'
    return {'rulesVersion':'2017-liquidity-20-research-1','conclusion':'比较确认净赎回与所填七个工作日可变现价值；变现价值需评估，账面市值不直接当成可变现现金。','status':status,'declaredGap':str(max(Decimal(0),redemption-liquid)),'source':LIQUIDITY,'clause':'§20/§40(2)','humanRows':[['确认净赎回',str(redemption)],['声明可变现价值',str(liquid)],['声明缺口',str(max(Decimal(0),redemption-liquid))]],'limitations':['不自动数交易日或保证卖出/到账；不将涨跌停简单判成必定不能成交','部分资料线内保留全范围未知；超出需复查估值及例外','不替代管理人的流动性评估及审批']}

if __name__=='__main__':raise SystemExit(cli({'dividend-tax':dividend_tax,'fund-limits':limits,'redemption-liquidity':redemption_liquidity},'投资规则与现金条件复查'))
