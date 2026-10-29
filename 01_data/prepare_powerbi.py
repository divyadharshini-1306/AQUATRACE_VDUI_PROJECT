"""Adds Power BI helper columns, EDA outlier flag and out-of-fold model probabilities to aquatrace_dataset.csv"""
import numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.inspection import permutation_importance
OUT='/mnt/user-data/outputs/'
d=pd.read_csv(OUT+'aquatrace_dataset.csv')

# --- region (for region -> country -> city drill-down) and sort-order helpers
R={'North America':['USA','Canada','Mexico'],
 'Europe':['Germany','United Kingdom','France','The Netherlands','Italy','Russia','Spain','Sweden','Ireland','Switzerland','Austria','Poland','Belgium','Denmark','Finland','Hungary','Ukraine'],
 'Asia-Pacific':['India','China','Japan','Singapore','Australia','Hong Kong','Malaysia','Taiwan','South Korea','Thailand','Vietnam'],
 'Middle East & Africa':['United Arab Emirates','Saudi Arabia','South Africa','Egypt','Algeria','Morocco','Nigeria','Kenya'],
 'Latin America':['Brazil','Argentina']}
cmap={c:r for r,cs in R.items() for c in cs}
d['Region']=d.Country.map(cmap)
assert d.Region.notna().all()
d['Risk_Tier_Order']=d.Water_Risk_Tier.map({'Low':1,'Medium':2,'High':3})
d['Stress_Tier_Order']=d.Stress_Tier_Baseline.map({'Low':1,'Moderate':2,'High':3,'Extreme':4})
d['Stress_Tier_3C_Order']=d.Stress_Tier_3C.map({'Low':1,'Moderate':2,'High':3,'Extreme':4})
d['Water_Stress_Index']=(d.Stress_Months_Baseline/12).round(3)
d['Water_Stress_Index_3C']=(d.Stress_Months_3C/12).round(3)
order=d.groupby('Cooling_System').WUE_L_per_kWh.mean().rank().astype(int)
d['Cooling_Order']=d.Cooling_System.map(order)

# --- EDA: WUE outlier flag within each cooling system (Tukey rule on log WUE)
lw=np.log(d.WUE_L_per_kWh)
g=lw.groupby(d.Cooling_System)
q1,q3=g.transform(lambda x:x.quantile(.25)),g.transform(lambda x:x.quantile(.75))
d['WUE_Outlier_Flag']=((lw<q1-1.5*(q3-q1))|(lw>q3+1.5*(q3-q1))).astype(int)

# --- model: out-of-fold P(High risk), grouped by facility. WUE / volume / score are EXCLUDED (they define the target)
feat=['Cooling_System','Climate_Zone','Facility_Type','IT_Capacity_MW','Utilization_Pct','AI_Workload_Share_Pct','Ambient_Temp_C','PUE','Stress_Tier_Order']
X=pd.get_dummies(d[feat],dtype=float); y=d.High_Risk
oof=np.zeros(len(d))
for tr,te in GroupKFold(5).split(X,y,d.Facility_ID):
    m=GradientBoostingClassifier(random_state=0).fit(X.iloc[tr],y.iloc[tr]); oof[te]=m.predict_proba(X.iloc[te])[:,1]
d['Pred_High_Risk_Prob']=oof.round(3)
d['Pred_High_Risk']=(oof>=.5).astype(int)
d['Model_Confidence']=np.maximum(oof,1-oof).round(3)
d['Low_Confidence_Flag']=(d.Model_Confidence<.8).astype(int)
d['Prediction_Error_Flag']=(d.Pred_High_Risk!=d.High_Risk).astype(int)
acc=(d.Pred_High_Risk==d.High_Risk).mean()

# --- grouped permutation importance + EDA correlation, for the "EDA vs model agree?" slide
m=GradientBoostingClassifier(random_state=0).fit(X,y)
r=permutation_importance(m,X,y,n_repeats=10,random_state=0,scoring='roc_auc'); imp=pd.Series(r.importances_mean,X.columns)
groups={'Cooling_System':[c for c in X if c.startswith('Cooling_System')],'Climate_Zone':[c for c in X if c.startswith('Climate_Zone')],
        'Facility_Type':[c for c in X if c.startswith('Facility_Type')]}
for k in ['IT_Capacity_MW','Utilization_Pct','AI_Workload_Share_Pct','Ambient_Temp_C','PUE','Stress_Tier_Order']: groups[k]=[k]
tab=pd.DataFrame({'Feature':list(groups),'Model_Importance':[imp[v].sum() for v in groups.values()]})
num={k:d[k].corr(d.Water_Risk_Score,method='spearman') for k in ['IT_Capacity_MW','Utilization_Pct','AI_Workload_Share_Pct','Ambient_Temp_C','PUE','Stress_Tier_Order']}
tab['EDA_Spearman_with_Risk_Score']=tab.Feature.map(num)
# categorical: eta-squared (share of risk-score variance explained)
for k in ['Cooling_System','Climate_Zone','Facility_Type']:
    gm=d.groupby(k).Water_Risk_Score; tab.loc[tab.Feature==k,'EDA_Variance_Explained']=((gm.transform('mean')-d.Water_Risk_Score.mean())**2).sum()/((d.Water_Risk_Score-d.Water_Risk_Score.mean())**2).sum()
tab=tab.sort_values('Model_Importance',ascending=False).round(3)
tab.to_csv(OUT+'model_importance.csv',index=False)
d.to_csv(OUT+'aquatrace_powerbi.csv',index=False)
print(d.shape,'oof acc',round(acc,3),'low-conf rows',d.Low_Confidence_Flag.sum(),'outliers',d.WUE_Outlier_Flag.sum(),'errors',d.Prediction_Error_Flag.sum())
print(tab.to_string(index=False))
