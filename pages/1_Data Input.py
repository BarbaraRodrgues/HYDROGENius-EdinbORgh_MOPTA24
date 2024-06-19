# User-defined Libraries
from auxiliary import InstanceMOPTA, ModelMOPTA, run_optimality_check
# Python Libraries
import os
import streamlit as st
from openpyxl import load_workbook
import pyomo.opt as pyo
import pyomo.environ as pyoenv
import pandas as pd

#-------------------------------------------------------------------------------
# Define and Initialize Session State defaults
if 'inst_type' not in st.session_state:
    st.session_state.inst_type = 'default'
if 'inst_filename' not in st.session_state:
    st.session_state.inst_filename = 'Instances\stochastic_instance_100_panels_20_percent.xlsx' #'Instances\stochastic_instance.xlsx' #'Instances\deterministic_instance.xlsx'
if 'inst_data' not in st.session_state:
    st.session_state.inst_data = InstanceMOPTA(st.session_state.inst_filename)

#-------------------------------------------------------------------------------
st.set_page_config(page_title="Data Input", page_icon=":eye:",
                   layout="wide", initial_sidebar_state="expanded")

#-------------------------------------------------------------------------------
st.header('Input Data Parameters')

instance_type = st.radio("What type of instance do you want to use?",
                         ["**Default Data**", "**User-defined Data**"],
                         captions = ["As described in the project's report.", "A file must be uploaded first."])

def update_instance_data():
    st.session_state.inst_data = InstanceMOPTA(st.session_state.inst_filename)

@st.cache_data
def run_model():
    # Run model and stora solution
    inst_data = st.session_state.get('inst_data')
    model = ModelMOPTA(inst_data)

    model.optimize()
    run_optimality_check(model)
    # Load solution to inst_data
    model.load_solution_inst()
    inst_data = model.inst 
    
    # Fix integer variables to compute duals
    LPmodel = model.fixed()
    # Re-run model
    LPmodel.optimize()
    run_optimality_check(LPmodel)

    # Export duals to instance
    inst_data.duals_E = pd.DataFrame.from_dict({s: LPmodel.getConstrByName(f"CmaxLossLoadElectricity[{s}]").Pi
                                                for s in model.inst.Scenarios}, orient='index')
    inst_data.duals_G = pd.DataFrame.from_dict({s: LPmodel.getConstrByName(f"CmaxLossLoadGas[{s}]").Pi
                                                for s in model.inst.Scenarios}, orient='index')
    
    st.session_state.inst_data = inst_data
    
if instance_type == "**User-defined Data**":
    #-------------------------------------------------------------------------------
    st.subheader('User-defined Data')
    st.session_state.inst_type = 'user-defined'

    col1, col2 = st.columns(2)

    # Upload Instance file
    uploaded_file = col1.file_uploader('Updoad Data Excel', type=['xlsx'])
    if uploaded_file:
        wb = load_workbook(uploaded_file)
        wb.save('Instances/current_instance.xlsx')
        st.session_state.inst_filename = 'Instances/current_instance.xlsx'

    # Download Instance Template
    cwd = os.getcwd()
    xlxs_name = 'Instances/template_instance.xlsx'
    xlxs_path = os.path.join(cwd, xlxs_name)
    col2.write('Download Template File Below')
    with open(xlxs_path, "rb") as f:
        col2.download_button(label='Template Data Excel', data=f, file_name='template_instance.xlsx')
else:
    #-------------------------------------------------------------------------------
    st.subheader('Default Data')
    st.write("The project's default data will be used. Please see the ***Data Visualization*** page for more details.")

#-------------------------------------------------------------------------------
st.header('Interact with Model')
st.write("Computing the solution might take a few minutes for the default instance\
          and more depending on the size of the problem.")

col1, col2, col3 = st.columns(3)
col1.button('Update and View Data', on_click=update_instance_data, use_container_width=True)
col2.button('Compute and View Solution', on_click=run_model, type="primary", use_container_width=True)
col2.metric(label="Status", value=st.session_state.inst_data.optimality_status)