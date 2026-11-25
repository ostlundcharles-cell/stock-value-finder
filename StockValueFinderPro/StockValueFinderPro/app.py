import streamlit as st
import yfinance as yf
import pandas as pd
import math, sqlite3, io
from pathlib import Path
from valuation import analyze
st.set_page_config(page_title='Stock Value Finder Pro',layout='wide')
DB=Path(__file__).with_name('watchlist.db')
def db():
    c=sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS watchlist (ticker TEXT PRIMARY KEY)'); return c

def num(x):
    try:
        x=float(x); return x if math.isfinite(x) else None
    except (ValueError,TypeError): return None
@st.cache_data(ttl=900,show_spinner=False)
def fetch(symbol):
    stock=yf.Ticker(symbol); i=stock.info
    p=num(i.get('currentPrice') or i.get('regularMarketPrice'))
    if not p: raise ValueError('Price unavailable; check ticker or retry later.')
    shares=num(i.get('sharesOutstanding')); f=num(i.get('freeCashflow'))
    currency=i.get('currency','Unknown'); financial=i.get('financialCurrency')
    same=currency==financial
    return dict(ticker=symbol,name=i.get('longName',symbol),price=p,currency=currency,financial_currency=financial,eps=num(i.get('trailingEps')) if same else None,fcf=f/shares if same and f is not None and shares and shares>0 else None,book=num(i.get('bookValue')) if same else None,roe=num(i.get('returnOnEquity')),de=num(i.get('debtToEquity')),growth=num(i.get('revenueGrowth')),sector=i.get('sector','Unknown'),industry=i.get('industry',''),total_fcf=f,shares=shares)
@st.cache_data(ttl=900)
def history(symbol): return yf.Ticker(symbol).history(period='1y',auto_adjust=False)
def fmt(x): return 'N/A' if x is None else f'{x:,.2f}'
def pct(x): return 'N/A' if x is None else f'{x:.1%}'
def export(df):
    b=io.BytesIO(); df.to_excel(b,index=False,engine='openpyxl'); return b.getvalue()
st.title('Stock Value Finder Pro')
st.caption('Global equity research • prices and fundamentals may be delayed • not investment advice')
with st.sidebar:
    st.header('Valuation assumptions')
    g=st.slider('5-year cash flow growth (%)',-20,30,3)/100
    r=st.slider('Required return (%)',8,25,12)/100
    t=st.slider('Terminal growth (%)',0,4,2)/100
    s=st.slider('Margin of safety (%)',10,60,25)/100
    pe=st.slider('Fair P/E multiple',5,40,15)
    if st.button('Refresh cached market data'): st.cache_data.clear()
args=(g,r,t,s,pe)
page=st.radio('Workspace',['Company analysis','Global scanner','Watchlist'],horizontal=True)
if page=='Company analysis':
    symbol=st.text_input('Yahoo Finance ticker','NVDA').strip().upper()
    if symbol:
        try:
            with st.spinner('Retrieving financial data…'): d=fetch(symbol); a=analyze(d,*args)
        except Exception as exc: st.error(str(exc)); st.stop()
        st.subheader(d['name']); st.caption(f"{symbol} | {d['sector']} | Quote currency: {d['currency']} | Reporting currency: {d['financial_currency']}")
        cols=st.columns(4)
        for col,label,val in zip(cols,['Market price','DCF fair value','Potential upside','Safety margin'],[fmt(d['price']),fmt(a['fair']),pct(a['upside']),pct(a['margin'])]): col.metric(label,val)
        st.subheader(a['verdict']); st.write('Maximum research entry price:',fmt(a['buy']))
        if d['currency']!=d['financial_currency']: st.warning('Currency mismatch or unknown reporting currency: per-share valuations disabled to avoid incorrect conversions (including GBp vs GBP).')
        if a['fair'] is None: st.warning('DCF unavailable: missing/negative cash flow or unsupported financial/REIT business.')
        st.bar_chart(pd.Series({k:v for k,v in {'Market':d['price'],'DCF':a['fair'],'Graham':a['graham'],'P/E':a['earnings']}.items() if v is not None}))
        st.write('Bear / base / bull DCF:',fmt(a['bear']), '/',fmt(a['fair']), '/',fmt(a['bull']))
        st.write('Market-implied five-year cash flow growth:',pct(a['reverse']))
        st.metric('Screening points (out of 100)',f"{a['score']} / 100",help='Missing inputs earn no points; this is not a probability or backtested score.')
        st.caption(f"Data coverage: {a['coverage']} / 100 weighted points")
        for label,known,ok,w in a['checks']: st.write(('✅' if ok and known else '⚠️' if known else '➖')+' '+label+(' — unavailable' if not known else ''))
        st.warning('Check for cyclical peak earnings, dilution, one-off cash flows, refinancing and declining demand before investing. Graham and P/E are cross-checks, not blended price targets.')
        st.dataframe(pd.DataFrame([{'Metric':k,'Value':str(v)} for k,v in d.items()]),hide_index=True)
        try:
            h=history(symbol)
            if not h.empty: st.line_chart(h['Close'])
        except Exception: st.info('Price history unavailable.')
        if st.button('Add to watchlist'):
            with db() as c: c.execute('INSERT OR IGNORE INTO watchlist VALUES (?)',(symbol,))
            st.success('Saved locally')
        st.download_button('Export valuation to Excel',export(pd.DataFrame([{**d,**{k:v for k,v in a.items() if k!='checks'}}])),f'{symbol}_valuation.xlsx')
else:
    if page=='Watchlist':
        with db() as c: symbols=[x[0] for x in c.execute('SELECT ticker FROM watchlist ORDER BY ticker')]
        if symbols:
            remove=st.selectbox('Remove ticker',symbols)
            if st.button('Remove'):
                with db() as c: c.execute('DELETE FROM watchlist WHERE ticker=?',(remove,))
                st.rerun()
    else:
        universes={'US':'AAPL MSFT NVDA GOOGL AMZN META PYPL CRM ADBE UHS MPC VLO LDOS LULU CVS','Europe':'SAP.DE SIE.DE BMW.DE BAS.DE ASML.AS MC.PA OR.PA TTE.PA NOVO-B.CO','Switzerland':'NESN.SW NOVN.SW ROG.SW ABBN.SW UBSG.SW SIKA.SW ZURN.SW','Asia-Pacific':'7203.T 6758.T 9984.T 0700.HK 9988.HK BHP.AX CBA.AX','Canada':'SHOP.TO CNQ.TO ENB.TO RY.TO'}
        regions=st.multiselect('Markets',list(universes),default=list(universes))
        custom=st.text_area('Additional tickers (spaces or commas)')
        symbols=list(dict.fromkeys((' '.join(universes[x] for x in regions)+' '+custom.replace(',',' ')).upper().split()))
    st.caption(f'{len(symbols)} tickers • sequential requests may take several minutes')
    if st.button('Run valuation scan',disabled=not symbols):
        rows=[]; progress=st.progress(0)
        for j,symbol in enumerate(symbols):
            try:
                d=fetch(symbol); a=analyze(d,*args)
                rows.append(dict(Ticker=symbol,Currency=d['currency'],Price=d['price'],Fair_value=a['fair'],Buy_below=a['buy'],Discount_pct=a['margin']*100 if a['margin'] is not None else None,Score=a['score'],Coverage=a['coverage'],Verdict=a['verdict']))
            except Exception as exc: rows.append(dict(Ticker=symbol,Verdict='DATA ERROR: '+str(exc)))
            progress.progress((j+1)/len(symbols))
        st.session_state['scan_'+page]=pd.DataFrame(rows)
    df=st.session_state.get('scan_'+page)
    if df is not None:
        st.caption('Last completed scan; rerun after changing assumptions or tickers.')
        if 'Discount_pct' in df: df=df.sort_values('Discount_pct',ascending=False,na_position='last')
        st.dataframe(df,hide_index=True); st.download_button('Export scan to Excel',export(df),'stock_scan.xlsx')
