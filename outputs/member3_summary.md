# Member 3 results (modelled estimates)

## audit
```
                                                           Model  accuracy  majority_baseline_acc  balanced_accuracy  recall_high  precision_high  f1_high  pr_auc  roc_auc  brier
                                    Member 1 column (GroupKFold)     0.977                  0.886              0.928        0.865           0.926    0.894   0.973    0.997  0.015
                         Member 3 OOF (StratifiedGroupKFold, gb)     0.980                  0.886              0.942        0.892           0.932    0.912   0.975    0.997  0.015
DEMO ONLY: with WUE + water use + stress weight (target leakage)     0.992                  0.886              0.973        0.949           0.978    0.963   0.996    0.999  0.006
                                Ablation: Stress_Tier_Order ONLY     0.925                  0.886              0.881        0.823           0.632    0.715   0.593    0.952  0.052
                   Ablation: everything EXCEPT Stress_Tier_Order     0.881                  0.886              0.522        0.057           0.347    0.098   0.255    0.757  0.095
```
## best_f1_threshold
```
(0.399, 0.924)
```
## shap_top_features
```
{'Stress_Tier_Order': 3.327, 'Cooling_System': 0.681, 'IT_Capacity_MW': 0.55, 'Ambient_Temp_C': 0.416, 'Facility_Type': 0.098, 'Utilization_Pct': 0.097, 'PUE': 0.067, 'Climate_Zone': 0.058, 'AI_Workload_Share_Pct': 0.015}
```
## importance
```
              Feature  Perm_Importance_OOF  SHAP_MeanAbs  EDA_Strength  Model_Rank  EDA_Rank      Verdict Divergence_Direction
    Stress_Tier_Order               0.8012        3.3267        0.2959           1         1        Agree                     
       Cooling_System               0.1627        0.6807        0.2070           2         2        Agree                     
       IT_Capacity_MW               0.1131        0.5503        0.1318           3         5 Partly agree                     
       Ambient_Temp_C               0.0419        0.4155        0.1414           4         4        Agree                     
        Facility_Type               0.0015        0.0980        0.0820           5         7 Partly agree                     
      Utilization_Pct               0.0010        0.0972        0.0918           6         6        Agree                     
                  PUE               0.0034        0.0671        0.0112           7         9 Partly agree                     
         Climate_Zone               0.0026        0.0579        0.1500           8         3      Diverge  EDA ranks it higher
AI_Workload_Share_Pct              -0.0001        0.0149        0.0289           9         8        Agree                     
```
## pca_explained_var
```
[0.334, 0.153]
```
## embed_method
```
UMAP
```
## drift_metrics
```
                                           Evaluation      n  high_share  pr_auc  recall_high  precision_high  f1_high
             OOF predictions on the same 2024-25 rows 2304.0       0.106   0.971        0.910           0.914    0.912
                     Temporal split: all 2024-25 rows 2304.0       0.106   0.988        0.996           0.900    0.946
Temporal split: only facilities first seen in 2024-25  250.0       0.104   0.965        1.000           0.839    0.912
```
## drift_psi
```
              Feature   PSI          PSI_Status
       Cooling_System 0.006       Stable (<0.1)
         Climate_Zone 0.001       Stable (<0.1)
        Facility_Type 0.059       Stable (<0.1)
       IT_Capacity_MW 0.041       Stable (<0.1)
      Utilization_Pct 0.195 Moderate (0.1-0.25)
AI_Workload_Share_Pct 1.806       Major (>0.25)
       Ambient_Temp_C 0.002       Stable (<0.1)
                  PUE 0.033       Stable (<0.1)
    Stress_Tier_Order 0.001       Stable (<0.1)
```
## drift_high_share
```
(np.float64(0.118), np.float64(0.106))
```
## bias_region
```
              Region  n_rows  n_facilities  n_countries  n_high_rows  n_high_facilities  false_positives  false_negatives  error_rate  low_confidence_share                                            status  recall  recall_lo  recall_hi  precision  precision_lo  precision_hi  pr_auc  pr_auc_lo  pr_auc_hi  accuracy  accuracy_lo  accuracy_hi
        Asia-Pacific    1348           242           11          261                 53               16               16      0.0237                0.0786                                                OK  0.9387     0.8931     0.9773     0.9387        0.8666        0.9902  0.9759     0.9426     0.9945    0.9763       0.9604       0.9894
              Europe    2270           419           17          124                 23                4               27      0.0137                0.0251                                                OK  0.7823     0.5998     0.9163     0.9604        0.9150        1.0000  0.9641     0.9149     0.9902    0.9863       0.9751       0.9947
       Latin America     189            37            2            0                  0                0                0      0.0000                0.0000 Insufficient data (0 High rows from 0 facilities)     NaN        NaN        NaN        NaN           NaN           NaN     NaN        NaN        NaN       NaN          NaN          NaN
Middle East & Africa     256            45            8          104                 18                3                8      0.0430                0.0898                                                OK  0.9231     0.7926     1.0000     0.9697        0.8720        1.0000  0.9956     0.9646     1.0000    0.9570       0.8985       1.0000
       North America    2449           457            3          251                 45               25               29      0.0220                0.0686                                                OK  0.8845     0.7902     0.9553     0.8988        0.8251        0.9647  0.9674     0.9340     0.9887    0.9780       0.9652       0.9877
```
## bias_other
```
              Group  n_rows  n_facilities  n_countries  n_high_rows  n_high_facilities  false_positives  false_negatives  error_rate  low_confidence_share                                             status  recall  recall_lo  recall_hi  precision  precision_lo  precision_hi  pr_auc  pr_auc_lo  pr_auc_hi  accuracy  accuracy_lo  accuracy_hi            Dimension
Air-Side Economizer    1941           350           34           43                  9                0               27      0.0139                0.0309 Insufficient data (43 High rows from 9 facilities)     NaN        NaN        NaN        NaN           NaN           NaN     NaN        NaN        NaN       NaN          NaN          NaN       Cooling_System
      Chilled Water    1978           355           38          348                 66               17               25      0.0212                0.0642                                                 OK  0.9282     0.8625     0.9768     0.9500        0.9097        0.9807  0.9810     0.9607     0.9929    0.9788       0.9664       0.9897       Cooling_System
        Evaporative     964           184           36          121                 25                7               14      0.0218                0.0332                                                 OK  0.8843     0.7307     1.0000     0.9386        0.8072        1.0000  0.9921     0.9648     1.0000    0.9782       0.9565       0.9990       Cooling_System
             Hybrid    1116           214           39          198                 44               19               13      0.0287                0.0941                                                 OK  0.9343     0.8839     0.9757     0.9069        0.8177        0.9708  0.9801     0.9574     0.9941    0.9713       0.9514       0.9855       Cooling_System
     Liquid Cooling     513           112           26           30                  7                5                1      0.0117                0.0585 Insufficient data (30 High rows from 7 facilities)     NaN        NaN        NaN        NaN           NaN           NaN     NaN        NaN        NaN       NaN          NaN          NaN       Cooling_System
      AI/HPC Campus     288           100           24           40                 12                1                4      0.0174                0.0625                                                 OK  0.9000     0.7077     1.0000     0.9730        0.8651        1.0000  0.9900     0.9440     1.0000    0.9826       0.9591       1.0000        Facility_Type
         Colocation    2303           409           38          386                 65                9               18      0.0117                0.0478                                                 OK  0.9534     0.9094     0.9941     0.9761        0.9538        0.9930  0.9894     0.9755     0.9984    0.9883       0.9794       0.9969        Facility_Type
               Edge     856           156           30           21                  3                2                1      0.0035                0.0175 Insufficient data (21 High rows from 3 facilities)     NaN        NaN        NaN        NaN           NaN           NaN     NaN        NaN        NaN       NaN          NaN          NaN        Facility_Type
         Enterprise    1801           292           40          155                 31               33               34      0.0372                0.0872                                                 OK  0.7806     0.6312     0.9081     0.7857        0.6481        0.9184  0.8905     0.7957     0.9558    0.9628       0.9421       0.9829        Facility_Type
         Hyperscale    1264           243           37          138                 28                3               23      0.0206                0.0427                                                 OK  0.8333     0.7042     0.9553     0.9746        0.9270        1.0000  0.9878     0.9694     0.9994    0.9794       0.9640       0.9935        Facility_Type
            Extreme     353            64           10          245                 46                7               14      0.0595                0.1246                                                 OK  0.9429     0.8834     0.9908     0.9706        0.9428        0.9946  0.9905     0.9759     0.9992    0.9405       0.8934       0.9845 Stress_Tier_Baseline
               High     611           107           12          364                 65               29               31      0.0982                0.2766                                                 OK  0.9148     0.8418     0.9745     0.9199        0.8552        0.9613  0.9795     0.9581     0.9925    0.9018       0.8469       0.9487 Stress_Tier_Baseline
                Low    4920           917           40            0                  0                0                0      0.0000                0.0000  Insufficient data (0 High rows from 0 facilities)     NaN        NaN        NaN        NaN           NaN           NaN     NaN        NaN        NaN       NaN          NaN          NaN Stress_Tier_Baseline
           Moderate     628           112           14          131                 28               12               35      0.0748                0.2245                                                 OK  0.7328     0.5555     0.8658     0.8889        0.7542        0.9805  0.8976     0.7857     0.9655    0.9252       0.8793       0.9598 Stress_Tier_Baseline
```
## ece
```
0.0102
```
## low_conf
```
0.0544
```
## errors
```
128
```
