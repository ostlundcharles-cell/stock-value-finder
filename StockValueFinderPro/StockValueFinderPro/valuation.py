import math

def dcf(fcf, growth, rate, terminal):
    if fcf is None or fcf <= 0 or rate <= terminal or growth <= -1: return None
    return sum(fcf*(1+growth)**i/(1+rate)**i for i in range(1,6)) + fcf*(1+growth)**5*(1+terminal)/(rate-terminal)/(1+rate)**5

def analyze(d,g=.03,r=.12,t=.02,s=.25,pe=15):
    p,e,f,b=d.get('price'),d.get('eps'),d.get('fcf'),d.get('book')
    if not p or p<=0: raise ValueError('No valid price')
    excluded=d.get('sector')=='Financial Services' or 'REIT' in d.get('industry','').upper()
    fair=None if excluded else dcf(f,g,r,t)
    graham=math.sqrt(22.5*e*b) if e and b and e>0 and b>0 else None
    earnings=e*pe if e and e>0 else None
    mos=1-p/fair if fair else None
    reverse=None
    if fair:
        lo,hi=-.8,1.
        if dcf(f,lo,r,t)<=p<=dcf(f,hi,r,t):
            for _ in range(60):
                mid=(lo+hi)/2
                if dcf(f,mid,r,t)<p: lo=mid
                else: hi=mid
            reverse=(lo+hi)/2
    checks=[('Positive earnings',e is not None,e is not None and e>0,15),('FCF yield >= 8%',f is not None and not excluded,f is not None and f/p>=.08,20),('Margin of safety met',mos is not None,mos is not None and mos>=s,30),('ROE >= 15%',d.get('roe') is not None,(d.get('roe') or 0)>=.15,15),('Debt/equity <= 100%',d.get('de') is not None and not excluded,0<= (d.get('de') if d.get('de') is not None else -1)<=100,10),('Revenue growth positive',d.get('growth') is not None,(d.get('growth') or 0)>0,10)]
    coverage=sum(w for _,known,_,w in checks if known)
    score=sum(w for _,known,ok,w in checks if known and ok)
    return dict(fair=fair,graham=graham,earnings=earnings,margin=mos,upside=fair/p-1 if fair else None,buy=fair*(1-s) if fair else None,reverse=reverse,bear=dcf(f,g-.05,r+.02,t) if fair else None,bull=dcf(f,g+.05,r-.02,t) if fair else None,score=score,coverage=coverage,checks=checks,verdict='MODEL NOT APPLICABLE / DATA MISSING' if fair is None else 'RESEARCH' if mos>=s else 'WATCH' if mos>=0 else 'ABOVE ESTIMATED VALUE')
