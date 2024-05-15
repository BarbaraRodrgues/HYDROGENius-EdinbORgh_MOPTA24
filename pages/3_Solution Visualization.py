# Python Libraries
import streamlit as st
import numpy as np
import pandas as pd
import math
import plotly.express as px

#-------------------------------------------------------------------------------
# Auxiliary Functions
def millify(n):
    millnames = ['',' Thousand',' Million',' Billion',' Trillion']
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])

def get_day(row):
    '''
    Function to get the day for each time_period
    '''
    inst_data = st.session_state.get('inst_data')
    df = pd.concat([inst_data.startPeriodOfDay, inst_data.endPeriodOfDay], axis=1).reset_index()
    for index, df_row in df.iterrows():
        if df_row['start_time_period'] <= row['Time Period'] <= df_row['end_time_period']:
            return df_row['day_id']
    return None
   
#-------------------------------------------------------------------------------
st.set_page_config(page_title="Solution Visualization", page_icon=":bulb:",
                   layout="wide", initial_sidebar_state="expanded")
st.title('Solution Visualisation')

# Global Data Parameters
inst_data = st.session_state.get('inst_data')

#-------------------------------------------------------------------------------
if inst_data.is_solution_loaded == False:
    st.write('The model must be first solved, for a solution to be visualised. Check the ***Data Input*** page below for more details.')
    st.page_link("pages/1_Data Input.py", label="Data Input", icon="👁️")
else:
    #-------------------------------------------------------------------------------
    scenario_options = tuple(inst_data.Scenario_names['scenario_name'])
    #day_options = tuple(['All']) + tuple(inst_data.Days)
    electrolyzer_options = tuple(inst_data.ElectrolyzerNodes)
    tank_options = tuple(inst_data.TankNodes)

    #-------------------------------------------------------------------------------
    st.header('Costs Breakdown')
    # Investement Costs (adding 0.0 to turn any -0 into 0)
    cost_build_solar = np.dot(np.array(inst_data.costBuildSolar), np.array(inst_data.buildNumSolar)) + 0.0
    cost_build_wind = np.dot(np.array(inst_data.costBuildWind), np.array(inst_data.buildNumWind)) + 0.0
    
    cost_build_storage_gas = np.dot(np.array(inst_data.costBuildStorageGas), np.array(inst_data.buildNumStorageGas)) + 0.0
    cost_build_storage_liquid = np.dot(np.array(inst_data.costBuildStorageLiquid), np.array(inst_data.buildNumStorageLiquid)) + 0.0

    total_investment = cost_build_solar + cost_build_wind + cost_build_storage_gas + cost_build_storage_liquid

    # Operational Costs
    cost_storage_gas_scenario = inst_data.costStorageGas * inst_data.storageGasSoc.groupby(level=[2]).sum()
    cost_storage_liquid_scenario = inst_data.costStorageLiquid * inst_data.storageLiquidSoc.groupby(level=[2]).sum()
    cost_storage_gas = np.dot(np.array(inst_data.scenarioWeight), np.array(cost_storage_gas_scenario)) + 0.0
    cost_storage_liquid = np.dot(np.array(inst_data.scenarioWeight), np.array(cost_storage_liquid_scenario)) + 0.0
    total_operational = cost_storage_gas + cost_storage_liquid

    col1, col2, col3 = st.columns(3)
    col1.metric(label="**Total Cost**", value=f"${millify(total_investment + total_operational)}")
    col2.metric(label="**Total Investment**", value=f"${millify(total_investment)}")
    col3.metric(label="**Total Operational**", value=f"${millify(total_operational)}")

    #-------------------------------------------------------------------------------
    st.subheader('Investement Costs')
    col1, col2 = st.columns(2)
    
    # Pie Plot of Investment Costs
    cost_list = [cost_build_solar, cost_build_wind, cost_build_storage_gas, cost_build_storage_liquid]
    cost_names = ['Cost Building Solar Plants', 'Cost Building Wind Plants',
                  'Cost Building Hydrogen Gas Storage','Cost Building Liquid Hydrogen Storage']
    df = pd.DataFrame(cost_list, index=cost_names, columns=['Cost Percentage'])
    df.index.name = 'Cost Type'
    df = df.apply(lambda x: 100*x/total_investment).reset_index()
    fig = px.pie(df, values = 'Cost Percentage', names = 'Cost Type')
    fig.update_traces(sort=False) 
    col1.plotly_chart(fig, theme="streamlit", use_container_width=True)
    
    # Values
    col2.write("##")
    col2.write("##")
    colA, colB = col2.columns(2)
    colA.metric(label="**Variable Cost Building Solar Plants**", value=f"${millify(cost_build_solar)}")
    colB.metric(label="**Variable Cost Building Wind Plants**", value=f"${millify(cost_build_wind)}")
    
    colA.metric(label="**Cost Building Hydrogen Gas Storage**", value=f"${millify(cost_build_storage_gas)}")
    colB.metric(label="**Cost Building Liquid Hydrogen Storage**", value=f"${millify(cost_build_storage_liquid)}")

    #-------------------------------------------------------------------------------
    st.subheader('Operational Costs')
    col1, col2 = st.columns(2)
    cost_storage_gas_scenario['storageGasSoc'] = cost_storage_gas_scenario['storageGasSoc'].apply(lambda x: millify(x))
    cost_storage_gas_scenario = cost_storage_gas_scenario.merge(inst_data.Scenario_names, left_on='Scenario', right_on='scenario_id')
    cost_storage_gas_scenario.columns = ['Operational Cost of Hydrogen Gas Storage','scenario_id', 'Scenario']
    cost_storage_gas_scenario = cost_storage_gas_scenario[['Scenario', 'Operational Cost of Hydrogen Gas Storage']].set_index('Scenario')
    cost_storage_liquid_scenario['storageLiquidSoc'] = cost_storage_liquid_scenario['storageLiquidSoc'].apply(lambda x: millify(x))
    cost_storage_liquid_scenario = cost_storage_liquid_scenario.merge(inst_data.Scenario_names, left_on='Scenario', right_on='scenario_id')
    cost_storage_liquid_scenario.columns = ['Operational Cost of Liquid Hydrogen Storage','scenario_id', 'Scenario']
    cost_storage_liquid_scenario = cost_storage_liquid_scenario[['Scenario', 'Operational Cost of Liquid Hydrogen Storage']].set_index('Scenario')    

    col1.dataframe(cost_storage_gas_scenario)
    col2.dataframe(cost_storage_liquid_scenario)

    #-------------------------------------------------------------------------------
    st.header('Installed Renewables')
    col1, col2 = st.columns(2)
    
    col1.subheader('Solar Plants')
    col2.subheader('Wind Plants')

    num_cadidate_solar = len(inst_data.SolarNodes)
    num_build_solar = np.count_nonzero(np.array(inst_data.buildNumSolar))
    col1.metric(label="**Number of Solar Plants Built**", value=f"{num_build_solar}/{num_cadidate_solar}")

    num_cadidate_wind = len(inst_data.WindNodes)
    num_build_wind = np.count_nonzero(np.array(inst_data.buildNumWind))
    col2.metric(label="**Number of Wind Plants Built**", value=f"{num_build_wind}/{num_cadidate_wind}")
    
    df = inst_data.buildNumSolar.reset_index()
    df = df.astype({'Solar Plant': 'str'})
    df = df.rename(columns={'Solar Plant': 'Solar Plant ID', 'buildNumSolar': '#Panel Rows Built'})
    fig = px.bar(df, x='Solar Plant ID' , y='#Panel Rows Built')
    col1.plotly_chart(fig, theme="streamlit", use_container_width=True)

    df = inst_data.buildNumWind.reset_index()
    df = df.astype({'Wind Plant': 'str'})
    df = df.rename(columns={'Wind Plant': 'Wind Plant ID', 'buildNumWind': '#Turbines Built'})
    fig = px.bar(df, x='Wind Plant ID' , y='#Turbines Built')
    col2.plotly_chart(fig, theme="streamlit", use_container_width=True)

    #-------------------------------------------------------------------------------
    st.subheader('Total Generation & Spillage')
    col1, col2, col3, col4 = st.columns(4)

    generation_scenario = col1.selectbox('Pick a scenario', scenario_options, key='generation_scenario')
    generation_scenario_id = inst_data.Scenario_names.loc[inst_data.Scenario_names['scenario_name'] == generation_scenario]['scenario_id'].iloc[0]
    
    # Sum over all locations for each (period, scenario) pair
    df1 = inst_data.generationRenewable.groupby(level=[1,2]).sum()
    df2 = inst_data.spillRenewable.groupby(level=[1,2]).sum()
    # Get generation and spillage data together and filter for scenario
    df = df1.join(df2).reset_index()
    max_gen = df['generationRenewable'].max()
    df = df.loc[df['Scenario'] == generation_scenario_id]
    # Create a new columns 'Day' and 'Time Period'
    df['Day'] = df.apply(get_day, axis=1)
    df['Time Period'] = df.groupby('Day').cumcount() + 1
    df = df.astype({'Day': 'str'})
    # Plot Data
    df = df.rename(columns={'generationRenewable': 'Installed Generation (MW)',
                            'spillRenewable':'Electricity Spillage (MW)'})

    tab1, tab2, tab3 = st.tabs(["Both", "Installed Generation", "Electricity Spillage"])
    with tab1:
        fig = px.line(df, x="Time Period", y=["Installed Generation (MW)", "Electricity Spillage (MW)"], color='Day')
        fig.update_traces(patch={"line": {"dash": "dot"}},
                          selector=lambda x: True if 'Electricity Spillage (MW)' in x['hovertemplate'] else False)
        fig.update_layout(yaxis=dict(range=[0, max_gen+10]))
        st.plotly_chart(fig, theme="streamlit")
    with tab2:
        fig = px.line(df, x="Time Period", y=["Installed Generation (MW)"], color='Day')
        fig.update_layout(yaxis=dict(range=[0, max_gen+10]))
        st.plotly_chart(fig, theme="streamlit")
    with tab3:
        fig = px.line(df, x="Time Period", y=["Electricity Spillage (MW)"], color='Day')
        fig.update_layout(yaxis=dict(range=[0, max_gen+10]))
        st.plotly_chart(fig, theme="streamlit")

    #-------------------------------------------------------------------------------
    st.header('Installed Storage')
    col1, col2 = st.columns(2)

    col1.subheader('Hydrogen Gas Storage Capacity')
    df = inst_data.buildNumStorageGas.reset_index()
    df = df.astype({'Electrolyzer': 'str'})
    df = df.rename(columns={'Electrolyzer': 'Electrolyzer ID', 'buildNumStorageGas': '#Gas Storage Tanks at Electrolyzer'})
    fig = px.bar(df, x='Electrolyzer ID' , y='#Gas Storage Tanks at Electrolyzer')
    col1.plotly_chart(fig, theme="streamlit", use_container_width=True)

    col2.subheader('Liquid Hydrogen Storage Capacity')
    df = inst_data.buildNumStorageLiquid.reset_index()
    df = df.astype({'Hydrogen Tank': 'str'})
    df = df.rename(columns={'Hydrogen Tank': 'Hydrogen Tank ID', 'buildNumStorageLiquid': '#Liquid Hydrogen Tanks'})
    fig = px.bar(df, x='Hydrogen Tank ID' , y='#Liquid Hydrogen Tanks')
    col2.plotly_chart(fig, theme="streamlit", use_container_width=True)

    #-------------------------------------------------------------------------------
    col1.subheader('Hydrogen Gas Storage Level')
    # Filters
    colA, colB = col1.columns(2)
    scenario_electrolyzer = colA.selectbox('Pick a scenario', scenario_options, key='electrolyzer')
    scenario_electrolyzer_id = inst_data.Scenario_names.loc[inst_data.Scenario_names['scenario_name'] == scenario_electrolyzer]['scenario_id'].iloc[0]
    electrolyzer_id = colB.selectbox('Pick an electrolyzer ID', electrolyzer_options)
    
    tab1, tab2 = col1.tabs(["Storage Level", "Charge vs. Discharge"])
    with tab1:
        # Get and Filter State of charge data
        df = inst_data.storageGasSoc
        df = df[(df.index.isin([electrolyzer_id], level=0)) & (df.index.isin([scenario_electrolyzer_id], level=2))]
        df = df.reset_index()
        # Create a new columns 'Day' and 'Time Period'
        df['Day'] = df.apply(get_day, axis=1)
        df['Time Period'] = df.groupby('Day').cumcount() + 1
        df = df.astype({'Day': 'str'})
        # Plot SoC
        df = df.rename(columns={'storageGasSoc':'Storage Level (MW)'})
        fig = px.line(df, x="Time Period", y="Storage Level (MW)", color='Day')
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    with tab2:
        # Plot Charge vs Discharge
        # Select electrolyzer ID and scenario
        df1 = inst_data.storageGasCharge
        df1 = df1[(df1.index.isin([electrolyzer_id], level=0)) & (df1.index.isin([scenario_electrolyzer_id], level=2))]
        df2 = inst_data.storageGasDischarge
        df2 = df2[(df2.index.isin([electrolyzer_id], level=0)) & (df2.index.isin([scenario_electrolyzer_id], level=2))]
        # Make discharge negative to plot in negative axis
        df2 = -df2 
        # Get charge and discharge data together
        df = df1.join(df2).reset_index()
        # New column to combine charge and discharge together
        df['Charged (MW)'] = np.where(df['storageGasCharge'] > 0, df['storageGasCharge'], df['storageGasDischarge'])
        # Create a new columns 'Day' and 'Time Period'
        df['Day'] = df.apply(get_day, axis=1)
        df['Time Period'] = df.groupby('Day').cumcount() + 1
        df = df.astype({'Day': 'str'})
        # Plot data
        fig = px.area(df, x="Time Period", y="Charged (MW)", color='Day')
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    #-------------------------------------------------------------------------------
    col2.subheader('Liquid Hydrogen Storage Level')
    # Filters
    colA, colB = col2.columns(2)
    scenario_tank = colA.selectbox('Pick a scenario', scenario_options, key='tank')
    scenario_tank_id = inst_data.Scenario_names.loc[inst_data.Scenario_names['scenario_name'] == scenario_tank]['scenario_id'].iloc[0]
    tank_id = colB.selectbox('Pick an tank ID', tank_options)

    tab1, tab2 = col2.tabs(["Storage Level", "Charge vs. Discharge"])
    with tab1:
        # Get and Filter State of charge data
        df = inst_data.storageLiquidSoc
        df = df[(df.index.isin([tank_id], level=0)) & (df.index.isin([scenario_tank_id], level=2))]
        df = df.reset_index()
        # Create a new columns 'Day' and 'Time Period'
        df['Day'] = df.apply(get_day, axis=1)
        df['Time Period'] = df.groupby('Day').cumcount() + 1
        df = df.astype({'Day': 'str'})
        # Plot SoC
        df = df.rename(columns={'storageLiquidSoc':'Storage Level (MW)'})
        fig = px.line(df, x="Time Period", y="Storage Level (MW)", color='Day')
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    with tab2:
        # Plot Charge vs Discharge
        # Select electrolyzer ID and scenario
        df1 = inst_data.storageLiquidCharge
        df1 = df1[(df1.index.isin([tank_id], level=0)) & (df1.index.isin([scenario_tank_id], level=2))]
        df2 = inst_data.storageLiquidDischarge
        df2 = df2[(df2.index.isin([tank_id], level=0)) & (df2.index.isin([scenario_tank_id], level=2))]
        # Make discharge negative to plot in negative axis
        df2 = -df2 
        # Get charge and discharge data together
        df = df1.join(df2).reset_index()
        # New column to combine charge and discharge together
        df['Charged (MW)'] = np.where(df['storageLiquidCharge'] > 0, df['storageLiquidCharge'], df['storageLiquidDischarge'])
        # Create a new columns 'Day' and 'Time Period'
        df['Day'] = df.apply(get_day, axis=1)
        df['Time Period'] = df.groupby('Day').cumcount() + 1
        df = df.astype({'Day': 'str'})
        # Plot data
        fig = px.area(df, x="Time Period", y="Charged (MW)", color='Day')
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    #-------------------------------------------------------------------------------
    st.header('Loss of Load Analysis')
    col1, col2 = st.columns(2)

    #-------------------------------------------------------------------------------
    col1.header('Loss of Electricity Load')

    max_lossload_perc = round(100 * inst_data.maxLossLoadElectricity, 3)
    col1.metric(label="**Maximum Loss of Load Allowed**", value=f"{max_lossload_perc}%")

    sol_lossload = inst_data.lossLoadElectricity.groupby(level=[2]).sum()
    sol_demand_sum = inst_data.demandElectricity.sum()
    sol_lossload["Solution's Loss Load"] = sol_lossload['lossLoadElectricity'].apply(
                                        lambda x: f"{round(100*x/sol_demand_sum, 3)}%")
    sol_lossload = sol_lossload[["Solution's Loss Load"]]

    # Add Shadow Prices
    df = inst_data.duals_E.reset_index()
    df = df.rename(columns={'index': 'scenario_id', 0: 'Shadow Prices'})
    df['Shadow Prices'] = np.abs(df['Shadow Prices']).round(decimals=2)
    sol_lossload = sol_lossload.merge(df, left_on='Scenario', right_on='scenario_id')

    # Add scenario names
    sol_lossload = sol_lossload.merge(inst_data.Scenario_names, left_on='scenario_id', right_on='scenario_id')
    sol_lossload = sol_lossload.rename(columns={'scenario_name': 'Scenario'})
    sol_lossload = sol_lossload.set_index('Scenario')
    sol_lossload = sol_lossload[["Solution's Loss Load", "Shadow Prices"]]
    
    col1.dataframe(sol_lossload)

    #-------------------------------------------------------------------------------
    col2.header('Loss of Gas Load')

    max_lossload_perc = round(100 * inst_data.maxLossLoadGas, 3)
    col2.metric(label="**Maximum Loss of Load Allowed**", value=f"{max_lossload_perc}%")

    sol_lossload = inst_data.lossLoadGas.groupby(level=[2]).sum()
    sol_demand_sum = inst_data.demandGas.sum()
    sol_lossload["Solution's Loss Load"] = sol_lossload['lossLoadGas'].apply(
                                        lambda x: f"{round(100*x/sol_demand_sum, 3)}%")
    sol_lossload = sol_lossload[["Solution's Loss Load"]]

    # Add Shadow Prices
    df = inst_data.duals_G.reset_index()
    df = df.rename(columns={'index': 'scenario_id', 0: 'Shadow Prices'})
    df['Shadow Prices'] = np.abs(df['Shadow Prices']).round(decimals=2)
    sol_lossload = sol_lossload.merge(df, left_on='Scenario', right_on='scenario_id')

    # Add scenario names
    sol_lossload = sol_lossload.merge(inst_data.Scenario_names, left_on='scenario_id', right_on='scenario_id')
    sol_lossload = sol_lossload.rename(columns={'scenario_name': 'Scenario'})
    sol_lossload = sol_lossload.set_index('Scenario')
    sol_lossload = sol_lossload[["Solution's Loss Load", "Shadow Prices"]]

    col2.dataframe(sol_lossload)
    
# END