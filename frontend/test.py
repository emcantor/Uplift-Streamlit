#%%#
from numpy import True_
import pandas as pd
#%%#
df_id = pd.read_csv('../scheduled.txt', sep='/n', header=None, engine='python', index_col=0)
print(df_id)
# %%
df_list = pd.read_json('../uplifts_data.json', orient='index')
#%%#
df_list[df_list['app_name'].str.lower().str.contains('santander', na=False)]
# %%#

#%%#