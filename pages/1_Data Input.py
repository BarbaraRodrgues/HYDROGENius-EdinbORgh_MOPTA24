# User-defined Libraries
from auxiliary import InstanceMOPTA, ModelMOPTA, fix_integer_variables, run_solve, run_optimality_check
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
    model = ModelMOPTA().build_inst(st.session_state.inst_data)
    opt = pyo.SolverFactory("gurobi_direct")
    results = opt.solve(model)
    inst_data.load_solution(results, model)
    
    # Fix integer variables to compute duals
    LPmodel = fix_integer_variables(model) 
    # Re-run model
    LPmodel.dual = pyoenv.Suffix(direction=pyoenv.Suffix.IMPORT_EXPORT) #Needed to export dual values later
    results2 = run_solve(LPmodel, warmstart=True)
    LPmodel = run_optimality_check(results2, LPmodel)
    # Export duals to instance
    inst_data.duals_E = pd.DataFrame.from_dict({s: LPmodel.dual[LPmodel.CmaxLossLoadElectricity[s]] 
                                                for s in LPmodel.Scenarios}, orient='index')
    inst_data.duals_G = pd.DataFrame.from_dict({s: LPmodel.dual[LPmodel.CmaxLossLoadGas[s]] 
                                                for s in LPmodel.Scenarios}, orient='index')
    
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
    xlxs_name = 'Instances/template_instance.xlsx' # TODO Replace with templace
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