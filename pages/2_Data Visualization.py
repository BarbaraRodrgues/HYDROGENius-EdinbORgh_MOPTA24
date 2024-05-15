# Python Libraries
import streamlit as st
import pandas as pd
import plotly.express as px

#-------------------------------------------------------------------------------
# Auxiliary Functions
# Function to get the day for each time_period
def get_day(row):
    inst_data = st.session_state.get('inst_data')
    df = pd.concat([inst_data.startPeriodOfDay, inst_data.endPeriodOfDay], axis=1).reset_index()
    for index, df_row in df.iterrows():
        if df_row['start_time_period'] <= row['time_period'] <= df_row['end_time_period']:
            return df_row['day_id']
    return None

#-------------------------------------------------------------------------------
st.set_page_config(page_title="Data Visualization", page_icon=":zap:",
                   layout="wide", initial_sidebar_state="expanded")
st.title('Data Visualization')

# Gloabal Data Parameters
inst_data = st.session_state.get('inst_data')

scenario_options = tuple(inst_data.Scenario_names['scenario_name'])
electrolyzer_options = tuple(inst_data.ElectrolyzerNodes)
tank_options = tuple(inst_data.TankNodes)

#-------------------------------------------------------------------------------
st.header('Overview of Network Locations')

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric(label="**Total:**", value=len(inst_data.Nodes))
col2.metric(label="**Electrolyzers:**", value=len(inst_data.ElectrolyzerNodes))
col3.metric(label="**Tanks:**", value=len(inst_data.TankNodes))
col4.metric(label="**Fuel Cells:**", value=len(inst_data.FuelCellNodes))
col1.metric(label="**Solar:**", value=len(inst_data.SolarNodes))
col2.metric(label="**Wind:**", value=len(inst_data.WindNodes))
col3.metric(label="**Industrial Areas:**", value=len(inst_data.IndustrialNodes))
col4.metric(label="**Residential Areas:**",
            value=len(inst_data.LoadNodes)-len(inst_data.IndustrialNodes))

#-------------------------------------------------------------------------------
st.header('Renewable Generation')

colA, colB, colC, colD = st.columns(4)
scenario_renewable = colA.selectbox('Pick a scenario', scenario_options, key='scenario_renewable')
scenario_renewable_id = inst_data.Scenario_names.loc[inst_data.Scenario_names['scenario_name'] == scenario_renewable]['scenario_id'].iloc[0]

#-------------------------------------------------------------------------------

col1, col2 = st.columns(2)
col1.subheader('Solar Generation')
col1.write('mean generation per solar panel row of installed capacity')

# Create dataframe
df = inst_data.generationSolar.groupby(level=[1,2]).mean().reset_index()
max_solar = df['generation'].max()
df = df.loc[df['scenario'] == scenario_renewable_id]
# Create a new columns 'Day' and 'Time Period'
df['Day'] = df.apply(get_day, axis=1)
df['Time Period'] = df.groupby('Day').cumcount() + 1
df = df.astype({'Day': 'str'})

# Filter scenario selected and plot
df = df.rename(columns={'generation': 'Generation (MWh/Panel Row)'})
fig = px.line(df, x="Time Period", y="Generation (MWh/Panel Row)", color="Day")
fig.update_layout(yaxis=dict(range=[0, max_solar*1.2]))
col1.plotly_chart(fig, theme="streamlit", use_container_width=True)

#-------------------------------------------------------------------------------
col2.subheader('Wind Generation')
col2.write('mean generation per wind turbine of installed capacity')

#colA, colB = col2.columns(2)
#scenario_wind = colA.selectbox('Pick a scenario', scenario_options, key='scenario_wind')

# Create dataframe
df = inst_data.generationWind.groupby(level=[1,2]).mean().reset_index()
max_wind = df['generation'].max()
df = df.loc[df['scenario'] == scenario_renewable_id]

# Create a new columns 'Day' and 'Time Period'
df['Day'] = df.apply(get_day, axis=1)
df['Time Period'] = df.groupby('Day').cumcount() + 1
df = df.astype({'Day': 'str'})

# Filter scenario selected and plot
df = df.rename(columns={'generation': 'Generation (MWh/Turbine)'})
fig = px.line(df, x="Time Period", y="Generation (MWh/Turbine)", color="Day")
fig.update_layout(yaxis=dict(range=[0, max_wind+0.1]))
col2.plotly_chart(fig, theme="streamlit", use_container_width=True)

#-------------------------------------------------------------------------------
st.header('Demand')

#-------------------------------------------------------------------------------
col1, col2 = st.columns(2)

col1.subheader('Electricity Demand')
col1.write('total demand over selected areas')

colA, colB = col1.columns(2)
load_type = colA.selectbox('Pick a type of area', ('All Areas', 'Residential Areas', 'Industrial Areas'), key='load_type')

if load_type == 'Industrial Areas':
    load_areas = list(inst_data.IndustrialNodes)
elif load_type == 'Residential Areas':
    load_areas = [item for item in list(inst_data.LoadNodes) if item not in list(inst_data.IndustrialNodes)]
else:
    load_areas = list(inst_data.LoadNodes)

# Create dataframe with sum of demand for selected areas
df = inst_data.demandElectricity
df = df[df.index.isin(load_areas, level=0)]
df = df.groupby(level=[1]).sum().reset_index()
# Create a new columns 'Day' and 'Time Period'
df['Day'] = df.apply(get_day, axis=1)
df['Time Period'] = df.groupby('Day').cumcount() + 1
df = df.astype({'Day': 'str'})
# Plot data
df = df.rename(columns={'demand': 'Demand (MWh)'})
fig = px.line(df, x="Time Period", y="Demand (MWh)", color="Day")
col1.plotly_chart(fig, theme="streamlit", use_container_width=True)

#-------------------------------------------------------------------------------
col2.subheader('Hydrogen Gas Demand')
col2.write('total demand over industrial areas')
col2.write("##")
col2.write("##")
col2.write("##")

# Create dataframe with sum of demand
df = inst_data.demandGas.groupby(level=[1]).sum().reset_index()
# Create a new columns 'Day' and 'Time Period'
df['Day'] = df.apply(get_day, axis=1)
df['Time Period'] = df.groupby('Day').cumcount() + 1
df = df.astype({'Day': 'str'})
# Plot data
df = df.rename(columns={'demand': 'Demand (MWh)'})
fig = px.line(df, x="Time Period", y="Demand (MWh)", color="Day")
col2.plotly_chart(fig, theme="streamlit", use_container_width=True)

#-------------------------------------------------------------------------------
st.header('Storage')
col1, col2 = st.columns(2)

#-------------------------------------------------------------------------------
col1.subheader('Hydrogen Gas')
col1.write('Intraday storage at the electrolyzers')

colA, colB = col1.columns(2)
electrolyzer = colA.selectbox('Pick an Electrolyzer Location', electrolyzer_options)

rate_selfdischarge = inst_data.selfDischargeStorageGas
rate_selfdischarge = f'{100*rate_selfdischarge[rate_selfdischarge.index.isin([electrolyzer])].iloc[0]} %'
eff_charging = inst_data.effChargingStorageGas
eff_charging = f'{100*eff_charging[eff_charging.index.isin([electrolyzer])].iloc[0]} %'
eff_discharging = inst_data.effDischargingStorageGas
eff_discharging = f'{100*eff_discharging[eff_discharging.index.isin([electrolyzer])].iloc[0]} %'
capacity = inst_data.capacityElectrolyzer
capacity = f'{capacity[capacity.index.isin([electrolyzer])].iloc[0]} MW'

df = pd.DataFrame({'Data Value': [rate_selfdischarge, eff_charging, eff_discharging, capacity]},
                   index=['Self-discharge Rate', 'Charging Efficiency', 'Discharging Efficiency',
                          'Storage Capacity'])
df.index.name = 'Name'
col1.dataframe(df)

#-------------------------------------------------------------------------------
col2.subheader('Liquid Hydrogen')
col2.write('Long-term at the hydrogen tanks')

colA, colB = col2.columns(2)
tank = colA.selectbox('Pick an Hydrogen Tank Location', tank_options)

rate_selfdischarge = inst_data.selfDischargeStorageLiquid
rate_selfdischarge = f'{100*rate_selfdischarge[rate_selfdischarge.index.isin([tank])].iloc[0]} %'
eff_charging = inst_data.effChargingStorageLiquid
eff_charging = f'{100*eff_charging[eff_charging.index.isin([tank])].iloc[0]} %'
eff_discharging = inst_data.effDischargingStorageLiquid
eff_discharging = f'{100*eff_discharging[eff_discharging.index.isin([tank])].iloc[0]} %'
capacity = inst_data.capacityTank
capacity = f'{capacity[capacity.index.isin([tank])].iloc[0]} MW'

df = pd.DataFrame({'Value': [rate_selfdischarge, eff_charging, eff_discharging, capacity]},
                   index=['Self-discharge Rate', 'Charging Efficiency', 'Discharging Efficiency', 
                          'Storage Capacity'])
df.index.name = 'Name'
col2.dataframe(df)

#-------------------------------------------------------------------------------
st.header('Conversion Rates and Process Efficiencies')

df = pd.DataFrame({'Value': [inst_data.conversionElectricityGas,
                            inst_data.conversionGasLiquid,
                            f"{100*inst_data.efficiencyElectrolysis}%",
                            f"{100*inst_data.efficiencyLiquefaction}%",
                            f"{100*inst_data.efficiencyGasification}%"]},
                   index=['Conversion Electricity (MW) -> Hydrogen Gas (kg)',
                          'Conversion Hydrogen Gas (MW) -> Liquid Hydrogen (kg)',
                          'Efficiency of Electrolysis Process',
                          'Efficiency of Liquefaction Process',
                          'Efficiency of Gasification Process'])
df.index.name = 'Name'
st.dataframe(df)

#-------------------------------------------------------------------------------
st.header('Capacities')#(Flow and Build)

capacity_solar  = inst_data.capacitySolar.agg(['min', 'mean', 'max']).reset_index().T[1:]
capacity_wind   = inst_data.capacityWind.agg(['min', 'mean', 'max']).reset_index().T[1:]
capacity_elect  = inst_data.capacityEdgeElectricity.agg(['min', 'mean', 'max']).reset_index().T[1:]
capacity_gas    = inst_data.capacityEdgeGas.agg(['min', 'mean', 'max']).reset_index().T[1:]
capacity_liquid = inst_data.capacityEdgeLiquid.agg(['min', 'mean', 'max']).reset_index().T[1:]

df = pd.concat([capacity_solar, capacity_wind, capacity_elect, capacity_gas, capacity_liquid])
df.columns = ['Minimum', 'Mean', 'Maximum']
df.index = ['Solar Plants (#Panels)', 'Wind Plants (#Turbines)', 
            'Electricity Grid Connections (MW)', 'Hydrogen Gas Grid Connections (MW)',
            'Liquid Hydrogen Grid Connections (MW)']
df.index.name = 'Capacity'

st.dataframe(df)

#-------------------------------------------------------------------------------
st.header('Costs')
col1, col2 = st.columns(2)

#-------------------------------------------------------------------------------
col1.subheader('Investment Costs')
col1.write('of building infrastructure')

build_solar = inst_data.costBuildSolar.agg(['min','mean','max']).reset_index().T[1:]
build_wind  = inst_data.costBuildWind.agg(['min','mean','max']).reset_index().T[1:]
build_gas_storage    = inst_data.costBuildStorageGas.agg(['min','mean','max']).reset_index().T[1:]
build_liquid_storage = inst_data.costBuildStorageLiquid.agg(['min','mean','max']).reset_index().T[1:]

df = pd.concat([build_solar, build_wind, build_gas_storage, build_liquid_storage])
df.columns = ['Minimum', 'Mean', 'Maximum']
df.index = ['Building Solar Plants (£/#Panels)', 'Building Wind Plants (£/#Turbines)',
            'Building Hydrogen Gas Storage (£/Tank)', 'Building Liquid Hydrogen Storage(£/Tank)']
df.index.name = 'Cost'

col1.dataframe(df)

#-------------------------------------------------------------------------------
col2.subheader('Operational Costs')
col2.write('of day-to-day management of storage systems')

df = pd.DataFrame({'Value': [inst_data.costStorageGas,
                            inst_data.costStorageLiquid]},
                   index=['Cost of Storing Hydrogen Gas (£/MW/time period)',
                          'Cost of Storing Liquid Hydrogen (£/MW/time period)'])
df.index.name = 'Name'
col2.dataframe(df)

#-------------------------------------------------------------------------------
st.header('Scenarios')
col1, col2 = st.columns(2)
# Pie Plot
df = inst_data.scenarioWeight.reset_index()
df = df.merge(inst_data.Scenario_names, left_on='scenario_id', right_on='scenario_id')

fig = px.pie(df, values = 'percent_weight', names = 'scenario_name',
             title='Weight of Scenarios for Operational Cost')#, hole = 0.2
col1.plotly_chart(fig, theme="streamlit")