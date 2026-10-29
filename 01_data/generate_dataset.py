"""
AquaTrace modelled dataset generator  (seed fixed -> fully reproducible)

REAL inputs (read from your uploads):
  - SummaryByCountry.xlsx : data centers per country, number of facilities in each
                            water-stress band (baseline and +3C), overlapping water-user sector
  - data_centre_wue.csv   : 90 real city/facility locations with lat/long, climate zone,
                            ambient temperature, humidity

MODELLED (estimated here, parameters calibrated to published figures - see DATA_CARD.md):
  facility type, capacity, cooling system, utilisation, AI share, PUE, WUE, daily energy/water,
  commissioning year, yearly panel 2019-2025, risk score/tier.

Every row is flagged Data_Basis = 'Modelled estimate'.
"""
import numpy as np, pandas as pd

UP = '/mnt/user-data/uploads/'
OUT = '/mnt/user-data/outputs/'
rng = np.random.default_rng(42)
N_FAC = 1200
YEARS = list(range(2019, 2026))

# ------------------------------------------------------------------ real inputs
wue = pd.read_csv(UP + 'data_centre_wue.csv')
country_of = {}
def m(names, c):
    for n in names: country_of[n] = c
m(['AWS Frankfurt','Frankfurt'],'Germany')
m(['AWS Oregon US','AWS Virginia US','Atlanta','Chicago','Equinix Virginia DC2','Google Iowa US','Google Oregon US','Houston','Iowa','Los Angeles','Meta Iowa US','Meta Oregon US','Microsoft Texas US','Microsoft Virginia US','Microsoft Washington US','Oregon','San Francisco','Virginia'],'USA')
m(['AWS Singapore','Equinix Singapore SG1','Google Singapore','Meta Singapore','Microsoft Singapore','Singapore'],'Singapore')
m(['AWS Stockholm','Lulea','Meta Sweden','Microsoft Sweden','Stockholm'],'Sweden')
m(['AWS Sydney','Microsoft Australia','Melbourne','Sydney'],'Australia')
m(['AWS Tokyo','Tokyo'],'Japan'); m(['Abu Dhabi','Dubai'],'United Arab Emirates')
m(['Algiers'],'Algeria'); m(['Amsterdam','Equinix Amsterdam AM3','Microsoft Netherlands'],'The Netherlands')
m(['Bangalore','Chennai','Delhi','Kolkata','Mumbai'],'India'); m(['Bangkok'],'Thailand')
m(['Beijing','Guangzhou','Shanghai'],'China'); m(['Budapest'],'Hungary'); m(['Buenos Aires'],'Argentina')
m(['Cairo'],'Egypt'); m(['Cape Town','Johannesburg'],'South Africa'); m(['Casablanca'],'Morocco')
m(['Google Belgium'],'Belgium'); m(['Google Finland','Helsinki'],'Finland'); m(['Google Taiwan','Taipei'],'Taiwan')
m(['Ho Chi Minh City'],'Vietnam'); m(['Hong Kong'],'Hong Kong'); m(['Jeddah'],'Saudi Arabia')
m(['Kuala Lumpur'],'Malaysia'); m(['Kyiv'],'Ukraine'); m(['Lagos'],'Nigeria')
m(['London','Manchester','Southampton'],'United Kingdom'); m(['Madrid'],'Spain')
m(['Meta Denmark','Viborg'],'Denmark'); m(['Mexico City'],'Mexico')
m(['Microsoft Canada Quebec','Montreal','Toronto','Vancouver'],'Canada'); m(['Microsoft Ireland'],'Ireland')
m(['Moscow'],'Russia'); m(['Nairobi'],'Kenya'); m(['Paris'],'France'); m(['Rome'],'Italy')
m(['Sao Paulo'],'Brazil'); m(['Seoul'],'South Korea'); m(['Vienna'],'Austria'); m(['Warsaw'],'Poland'); m(['Zurich'],'Switzerland')

DROP = {'AWS','Google','Meta','Microsoft','Equinix','US','AM3','SG1','DC2'}
def city(n):
    t = [w for w in n.split() if w not in DROP]
    return ' '.join(t) if t else n

loc = (wue.groupby('Data_Centre_Name')
       .agg(Latitude=('Latitude','mean'), Longitude=('Longitude','mean'),
            Climate_Zone=('Climate_Zone', lambda x: x.mode()[0]),
            T=('Ambient_Temperature_C','mean'), RH=('Relative_Humidity_Pct','mean')).reset_index())
loc['Country'] = loc.Data_Centre_Name.map(country_of)
loc['City'] = loc.Data_Centre_Name.map(city)
loc = loc.drop_duplicates(['City','Country']).reset_index(drop=True)

s = pd.read_excel(UP + 'SummaryByCountry.xlsx', sheet_name='Summary by country', header=None, skiprows=2).iloc[:, :16]
s.columns = ['Country','N','b0','b1','b2','b3','t0','t1','t2','t3','Municipal','Electricity','Livestock','Manufacturing','Mining','Irrigation']
s = s[s.Country.notna() & (s.Country != 'Global')].set_index('Country')
sectors = ['Municipal','Electricity','Livestock','Manufacturing','Mining','Irrigation']
s['Main_Overlap_Sector'] = s[sectors].astype(float).idxmax(axis=1)

countries = sorted(set(loc.Country) & set(s.index))

# ------------------------------------------------------------------ facilities per country
w = np.array([s.loc[c, 'N'] ** 0.85 for c in countries])
raw = w / w.sum() * N_FAC
cnt = np.maximum(3, np.floor(raw).astype(int))
while cnt.sum() < N_FAC:
    cnt[np.argmax(raw - cnt)] += 1
while cnt.sum() > N_FAC:
    cnt[np.argmax(cnt - raw)] -= 1
alloc = dict(zip(countries, cnt))

# ------------------------------------------------------------------ facility types
TYPES = ['Hyperscale','Colocation','Enterprise','Edge','AI/HPC Campus']
T_P   = [0.22, 0.33, 0.24, 0.13, 0.08]
T_CAP = {'Hyperscale':(60,0.55,20,300), 'Colocation':(15,0.55,5,80), 'Enterprise':(4,0.5,1,20),
         'Edge':(1.2,0.4,0.5,5), 'AI/HPC Campus':(120,0.5,50,500)}      # median, sigma, min, max (MW IT)
T_UTIL = {'Hyperscale':66,'Colocation':60,'Enterprise':48,'Edge':42,'AI/HPC Campus':72}
T_GROW = {'Hyperscale':0.04,'Colocation':0.02,'Enterprise':0.0,'Edge':0.02,'AI/HPC Campus':0.06}
T_AI   = {'Hyperscale':0.45,'Colocation':0.25,'Enterprise':0.08,'Edge':0.10,'AI/HPC Campus':0.95}
T_START= {'Hyperscale':2010,'Colocation':2008,'Enterprise':2008,'Edge':2012,'AI/HPC Campus':2020}
T_G    = {'Hyperscale':0.03,'Colocation':0.02,'Enterprise':-0.03,'Edge':0.03,'AI/HPC Campus':0.15}
SUFFIX = {'Hyperscale':'Campus','Colocation':'Colo','Enterprise':'Enterprise DC','Edge':'Edge Site','AI/HPC Campus':'AI Campus'}

COOL = ['Evaporative','Chilled Water','Air-Side Economizer','Hybrid','Liquid Cooling']
C_BASE = {'Hyperscale':[.30,.10,.25,.25,.10], 'Colocation':[.25,.40,.12,.18,.05], 'Enterprise':[.08,.50,.22,.15,.05],
          'Edge':[.02,.30,.60,.05,.03], 'AI/HPC Campus':[.12,.12,.05,.21,.50]}
COLD = {'subarctic','continental','oceanic'}; HOT = {'tropical','desert'}

# WUE (onsite, L per kWh of IT energy) - mean by cooling system
W_BASE = {'Evaporative':1.45,'Chilled Water':0.85,'Hybrid':0.55,'Air-Side Economizer':0.15,'Liquid Cooling':0.20}
P_BASE = {'Evaporative':1.25,'Chilled Water':1.45,'Hybrid':1.28,'Air-Side Economizer':1.20,'Liquid Cooling':1.15}
P_TYPE = {'Hyperscale':-0.08,'AI/HPC Campus':-0.05,'Colocation':0.0,'Enterprise':0.15,'Edge':0.20}
W_TYPE = {'Hyperscale':0.85,'AI/HPC Campus':0.9,'Colocation':1.0,'Enterprise':1.05,'Edge':1.1}

def band_from(u, counts):
    p = np.cumsum(np.asarray(counts, float) / np.sum(counts))
    return int(np.searchsorted(p, u, side='right').clip(0, 3))
BAND_MONTHS = {0:(0,0), 1:(1,4), 2:(5,8), 3:(9,12)}
TIER = {0:'Low', 1:'Moderate', 2:'High', 3:'Extreme'}

rows = []
fid = 0
for c in countries:
    cities = loc[loc.Country == c].reset_index(drop=True)
    sc = s.loc[c]
    base_counts = sc[['b0','b1','b2','b3']].astype(float).values
    c3_counts = sc[['t0','t1','t2','t3']].astype(float).values
    for _ in range(alloc[c]):
        fid += 1
        L = cities.iloc[rng.integers(len(cities))]
        ftype = rng.choice(TYPES, p=T_P)
        # stress band: sampled from the REAL country distribution; same quantile for +3C (monotone coupling)
        u = rng.random()
        b_base, b_3c = band_from(u, base_counts), band_from(u, c3_counts)
        b_3c = max(b_base, b_3c)
        m_base = rng.integers(BAND_MONTHS[b_base][0], BAND_MONTHS[b_base][1] + 1)
        m_3c = max(m_base, rng.integers(BAND_MONTHS[b_3c][0], BAND_MONTHS[b_3c][1] + 1))
        # cooling choice depends on facility type, climate and local water stress
        p = np.array(C_BASE[ftype], float)
        if L.Climate_Zone in COLD: p *= np.array([.8,1,2.5,1,1])
        if L.Climate_Zone in HOT:  p *= np.array([1.2,1,.3,1,1])
        if b_base >= 2:            p *= np.array([.6,1,1,1.4,1.3])
        cool = rng.choice(COOL, p=p / p.sum())
        # capacity
        med, sg, lo, hi = T_CAP[ftype]
        cap0 = float(np.clip(rng.lognormal(np.log(med), sg), lo, hi))
        # commissioning year
        ys = np.arange(T_START[ftype], 2026)
        wy = np.exp(T_G[ftype] * (ys - T_START[ftype]))
        comm = int(rng.choice(ys, p=wy / wy.sum()))
        lat = L.Latitude + rng.normal(0, 0.05); lon = L.Longitude + rng.normal(0, 0.05)
        f_util = rng.normal(0, 6); f_wue = rng.normal(0, 0.15); f_pue = rng.normal(0, 0.03)
        cur_cool = cool
        for y in YEARS:
            if y < comm: continue
            age = y - comm
            # retrofit away from water-intensive cooling in stressed regions
            if y >= 2022 and cur_cool in ('Evaporative','Chilled Water') and b_base >= 2 and rng.random() < 0.06:
                cur_cool = 'Hybrid'
            ramp = [0.45, 0.75, 0.95][age] if age < 3 else 1.0
            cap = cap0 * ramp * (1 + T_GROW[ftype]) ** max(0, y - max(comm, 2019))
            ai = np.clip(T_AI[ftype] / (1 + np.exp(-(y - 2023) * 0.8)) + rng.normal(0, 0.03), 0, 0.98)
            util = np.clip(T_UTIL[ftype] + 0.6 * (y - 2019) + 10 * ai + f_util + rng.normal(0, 2) - (8 if age == 0 else 0), 25, 95)
            temp = L['T'] + 0.03 * (y - 2019) + rng.normal(0, 0.4)
            rh = float(np.clip(L.RH + rng.normal(0, 2), 10, 98))
            # WUE
            wv = W_BASE[cur_cool] * W_TYPE[ftype]
            if cur_cool in ('Evaporative','Chilled Water','Hybrid'): wv *= np.exp(0.045 * (temp - 15))
            elif cur_cool == 'Air-Side Economizer': wv *= np.exp(0.08 * (temp - 15)) * (1 + 0.004 * max(0, rh - 60))
            else: wv *= np.exp(0.02 * (temp - 15))
            if cur_cool != 'Liquid Cooling': wv *= (1 + 0.25 * ai)
            wv *= 0.98 ** (y - 2019) * np.exp(f_wue + rng.normal(0, 0.08)) * (1 - 0.002 * (util - 60))
            wv = float(np.clip(wv, 0.01, 4.0))
            # PUE
            pv = P_BASE[cur_cool] + P_TYPE[ftype] + (0.008 if cur_cool == 'Air-Side Economizer' else 0.004) * (temp - 15) - 0.004 * (y - 2019) + f_pue + rng.normal(0, 0.03)
            pv = float(np.clip(pv, 1.05, 2.2))
            it_mwh = cap * util / 100 * 24
            rows.append(dict(
                Facility_ID=f'DC-{fid:04d}', Facility_Name=f'{L.City} {SUFFIX[ftype]} {fid:04d}', Year=y,
                Country=c, City=L.City, Latitude=round(lat, 3), Longitude=round(lon, 3), Climate_Zone=L.Climate_Zone,
                Facility_Type=ftype, Year_Commissioned=comm, Cooling_System=cur_cool,
                IT_Capacity_MW=round(cap, 2), Utilization_Pct=round(util, 1), AI_Workload_Share_Pct=round(ai * 100, 1),
                Ambient_Temp_C=round(temp, 1), Relative_Humidity_Pct=round(rh, 1),
                PUE=round(pv, 3), WUE_L_per_kWh=round(wv, 3),
                Daily_Electricity_MWh=round(it_mwh * pv, 1), Daily_Water_Use_m3=round(it_mwh * wv, 1),
                Stress_Months_Baseline=int(m_base), Stress_Tier_Baseline=TIER[b_base],
                Stress_Months_3C=int(m_3c), Stress_Tier_3C=TIER[b_3c],
                Main_Overlap_Sector=sc.Main_Overlap_Sector, Data_Basis='Modelled estimate'))

df = pd.DataFrame(rows)

# ------------------------------------------------------------------ water-stress-weighted risk
w_map = {'Low':0.0, 'Moderate':0.35, 'High':0.7, 'Extreme':1.0}
df['Stress_Weight'] = df.Stress_Tier_Baseline.map(w_map)
df['WUE_Pctile'] = df.WUE_L_per_kWh.rank(pct=True)
df['Volume_Pctile'] = df.Daily_Water_Use_m3.rank(pct=True)
df['Water_Risk_Score'] = (100 * (0.25 + 0.75 * df.Stress_Weight) * (0.5 * df.WUE_Pctile + 0.5 * df.Volume_Pctile)).round(1)
df['Water_Risk_Tier'] = pd.cut(df.Water_Risk_Score, [-1, 20, 35, 101], labels=['Low','Medium','High']).astype(str)
df['High_Risk'] = (df.Water_Risk_Tier == 'High').astype(int)
df = df.drop(columns=['WUE_Pctile','Volume_Pctile'])

df.to_csv(OUT + 'aquatrace_dataset.csv', index=False)
print(df.shape, df.Facility_ID.nunique(), 'facilities')
