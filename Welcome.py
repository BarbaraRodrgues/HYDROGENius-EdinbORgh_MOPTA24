"""
@author: Bárbara Rodrigues, Daniel Kopisitskiy, Denise Cariaga Sandoval
@project: MOPTA Competition 2024 Project
"""

# Python Libraries
import os
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

#-------------------------------------------------------------------------------
st.set_page_config(page_title="EdinbORgh Hydrogeniuses UI", page_icon=":closed_book:",
                   layout="centered", initial_sidebar_state="expanded")
st.title('The Potential of Green Hydrogen')
st.subheader("Team: HYDROGENius EdinbORgh")
st.write("**Bárbara Rodrigues, Daniel Kopisitskiy, Denise Cariaga Sandoval**")

st.page_link("pages/1_Data Input.py", label="Data Input", icon="👁️")
st.page_link("pages/2_Data Visualization.py", label="Data Visualization", icon="⚡")
st.page_link("pages/3_Solution Visualization.py", label="Solution Visualization", icon="💡")

#-------------------------------------------------------------------------------
st.header('Documentation')

cwd = os.getcwd()
pdf_name = 'HYDROGENius_EdinbORgh_MOPTA24_Report.pdf'
pdf_path = os.path.join(cwd, pdf_name)

col1, col2 = st.columns(2)
col1.write("Read and download this project's report.")
col3, col4 = col2.columns(2)
with open(pdf_path, "rb") as f:
    col4.download_button(label='Project Report (pdf)', data=f, file_name='HYDROGENius_EdinbORgh_MOPTA24_Report.pdf')
pdf_viewer(pdf_name, height=500)