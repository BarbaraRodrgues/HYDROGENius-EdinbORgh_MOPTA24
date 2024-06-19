"""
@author: Bárbara Rodrigues, Daniel Kopisitskiy, Denise Cariaga Sandoval
@project: MOPTA Competition 2024 Project
"""
# Python Libraries
import gurobipy as gp
from gurobipy import GRB

import pyomo.environ as pyo
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition

import pandas as pd
import numpy as np
from dataclasses import dataclass
import matplotlib.pyplot as plt

@dataclass
class InstanceMOPTA():
    ## Parameter Data
    # Sets
    Days        : set
    TimePeriods : set
    Nodes       : set
    Scenarios   : set	

    SolarNodes        : set
    WindNodes         : set
    RenewableNodes    : set
    ElectrolyzerNodes : set
    TankNodes         : set
    FuelCellNodes     : set
    LoadNodes         : set
    IndustrialNodes   : set

    Scenario_names : pd.DataFrame = pd.DataFrame()

    # Parameters
    costBuildSolar : pd.DataFrame = pd.DataFrame()
    capacitySolar  : pd.DataFrame = pd.DataFrame()
    costBuildWind  : pd.DataFrame = pd.DataFrame()
    capacityWind   : pd.DataFrame = pd.DataFrame()

    selfDischargeStorageGas  : pd.DataFrame = pd.DataFrame()
    effChargingStorageGas    : pd.DataFrame = pd.DataFrame()
    effDischargingStorageGas : pd.DataFrame = pd.DataFrame()
    capacityElectrolyzer     : pd.DataFrame = pd.DataFrame()
    maxChargeElectrolyzer    : pd.DataFrame = pd.DataFrame()
    costBuildStorageGas      : pd.DataFrame = pd.DataFrame()

    selfDischargeStorageLiquid  : pd.DataFrame = pd.DataFrame()
    effChargingStorageLiquid    : pd.DataFrame = pd.DataFrame()
    effDischargingStorageLiquid : pd.DataFrame = pd.DataFrame()
    capacityTank                : pd.DataFrame = pd.DataFrame()
    maxChargeTank               : pd.DataFrame = pd.DataFrame()
    costBuildStorageLiquid      : pd.DataFrame = pd.DataFrame()

    df_day_of_period : pd.DataFrame = pd.DataFrame()
    startPeriodOfDay : pd.DataFrame = pd.DataFrame()
    endPeriodOfDay   : pd.DataFrame = pd.DataFrame()
    scenarioWeight : pd.DataFrame = pd.DataFrame()

    capacityEdgeElectricity : pd.DataFrame = pd.DataFrame()
    capacityEdgeElectricity : pd.DataFrame = pd.DataFrame()
    capacityEdgeLiquid      : pd.DataFrame = pd.DataFrame()

    demandElectricity : pd.DataFrame = pd.DataFrame()
    demandGas         : pd.DataFrame = pd.DataFrame()

    generationSolar : pd.DataFrame = pd.DataFrame()
    generationWind  : pd.DataFrame = pd.DataFrame()	

    conversionGasLiquid      : float = 1
    conversionElectricityGas : float = 1
    efficiencyElectrolysis   : float = 1
    efficiencyLiquefaction   : float = 1
    efficiencyGasification   : float = 1
    maxLossLoadElectricity   : float = 0
    maxLossLoadGas           : float = 0
    costStorageGas           : float = 0
    costStorageLiquid        : float = 0

    ## Solution Values
    is_solution_loaded : bool = False
    optimality_status: str = 'Not Yet Solved'

    # First Stage Decisions
    buildNumSolar          : pd.DataFrame = pd.DataFrame()	
    buildNumWind           : pd.DataFrame = pd.DataFrame()	
    buildNumStorageGas     : pd.DataFrame = pd.DataFrame()	
    buildNumStorageLiquid  : pd.DataFrame = pd.DataFrame()	
    # Flow Decisions
    flowElectricity : pd.DataFrame = pd.DataFrame()	
    flowGas         : pd.DataFrame = pd.DataFrame()	
    flowLiquid      : pd.DataFrame = pd.DataFrame()	
    lossLoadElectricity : pd.DataFrame = pd.DataFrame()	
    lossLoadGas         : pd.DataFrame = pd.DataFrame()	
    # Generation Decision
    generationRenewable : pd.DataFrame = pd.DataFrame()	
    spillRenewable      : pd.DataFrame = pd.DataFrame()	
    # Storage Decisions
    storageGasSoc       : pd.DataFrame = pd.DataFrame()	
    storageGasCharge    : pd.DataFrame = pd.DataFrame()	
    storageGasDischarge : pd.DataFrame = pd.DataFrame()	
    storageLiquidSoc       : pd.DataFrame = pd.DataFrame()	
    storageLiquidCharge    : pd.DataFrame = pd.DataFrame()	
    storageLiquidDischarge : pd.DataFrame = pd.DataFrame()

    duals_E : pd.DataFrame = pd.DataFrame()
    duals_G : pd.DataFrame = pd.DataFrame()

    def __init__(self, filename:str):
        '''
        Input:
            filename - Name of the xlsx instance file
        '''
        # Read file into dictionary of dataframes for each sheet
        sheets_list = ['vertices', 'solar_params', 'wind_params', 'electrolyzer_params', 'tank_params', 'fuelcell_params',
            'electricityloads', 'industrialloads', 'time_params', 'day_params', 'scenario_params', 'electricity_edges',
            'gas_edges', 'liquid_edges', 'electricity_demand', 'gas_demand', 'solar_generation', 'wind_generation', 'scalar_params']
        dict_pd = pd.read_excel(filename, sheet_name=sheets_list)

        # Initialise Sets Data
        self.Days        = set(dict_pd['day_params']['day_id'])
        self.TimePeriods = set(dict_pd['time_params']['time_period_id'])
        self.Nodes       = set(dict_pd['vertices']['vertex_id'])
        self.Scenarios   = set(dict_pd['scenario_params']['scenario_id'])
        self.Scenario_names = dict_pd['scenario_params'][['scenario_id', 'scenario_name']]

        self.SolarNodes        = set(dict_pd['solar_params']['solar_panel_id'])
        self.WindNodes         = set(dict_pd['wind_params']['wind_turbine_id'])
        self.RenewableNodes    = self.SolarNodes.union(self.WindNodes)
        self.ElectrolyzerNodes = set(dict_pd['electrolyzer_params']['electrolyzer_id'])
        self.TankNodes         = set(dict_pd['tank_params']['liquid_tank_id'])
        self.FuelCellNodes     = set(dict_pd['fuelcell_params']['fuel_cell_id'])
        self.LoadNodes         = set(dict_pd['electricityloads']['electricity_loads_id'])
        self.IndustrialNodes   = set(dict_pd['industrialloads']['industrial_loads_id'])

        # Initialise Data in sheet 'solar_params'
        df_temp = dict_pd['solar_params'].set_index(['solar_panel_id'])
        self.costBuildSolar = df_temp['cost_building_solarpanel']
        self.capacitySolar  = df_temp['max_building_capacity']

        # Initialise Data in sheet 'wind_params'
        df_temp = dict_pd['wind_params'].set_index(['wind_turbine_id'])
        self.costBuildWind = df_temp['cost_building_turbine']
        self.capacityWind  = df_temp['max_building_capacity']

        # Initialise Data in sheet 'electrolyzer_params'
        df_temp = dict_pd['electrolyzer_params'].set_index(['electrolyzer_id'])
        self.selfDischargeStorageGas  = df_temp['self_discharge_rate_gas_tank']
        self.effChargingStorageGas    = df_temp['charge_efficiency_gas_tank']
        self.effDischargingStorageGas = df_temp['discharge_efficiency_gas_tank']
        self.capacityElectrolyzer     = df_temp['capacity_per_gas_tank']
        self.maxChargeElectrolyzer    = df_temp['max_charge_gas_tank']
        self.costBuildStorageGas      = df_temp['cost_per_gas_tank']

        # Initialise Data in sheet 'tank_params'
        df_temp = dict_pd['tank_params'].set_index(['liquid_tank_id'])
        self.selfDischargeStorageLiquid  = df_temp['self_discharge_rate_liquid_tank']
        self.effChargingStorageLiquid    = df_temp['charge_efficiency_liquid_tank']
        self.effDischargingStorageLiquid = df_temp['discharge_efficiency_liquid_tank']
        self.capacityTank                = df_temp['capacity_per_liquid_tank']
        self.maxChargeTank               = df_temp['max_charge_liquid_tank']
        self.costBuildStorageLiquid      = df_temp['cost_per_liquid_tank']

        # Initialise Data in sheet 'time_params'
        self.df_day_of_period = dict_pd['time_params'].set_index(['time_period_id'])

        # Initialise Data in sheet 'day_params'
        df_temp = dict_pd['day_params'].set_index(['day_id'])
        self.startPeriodOfDay = df_temp['start_time_period']
        self.endPeriodOfDay   = df_temp['end_time_period']

        # Initialise Data in sheet 'scenario_params'
        df_temp = dict_pd['scenario_params'].set_index(['scenario_id'])
        self.scenarioWeight = df_temp['percent_weight']

        # Initialise Data in sheet 'electricity_edges'
        df_temp = dict_pd['electricity_edges'].set_index(['vertex_from','vertex_to'])
        self.capacityEdgeElectricity = df_temp['max_electricity_flow']

        # Initialise Data in sheet 'gas_edges'
        df_temp = dict_pd['gas_edges'].set_index(['vertex_from','vertex_to'])
        self.capacityEdgeGas = df_temp['max_gas_flow']

        # Initialise Data in sheet 'liquid_edges'
        df_temp = dict_pd['liquid_edges'].set_index(['vertex_from','vertex_to'])
        self.capacityEdgeLiquid = df_temp['max_liquid_flow']

        # Initialise Data in sheet 'electricity_demand'
        df_temp = dict_pd['electricity_demand'].set_index(['vertex','time_period'])
        self.demandElectricity = df_temp['demand']

        # Initialise Data in sheet 'gas_demand'
        df_temp = dict_pd['gas_demand'].set_index(['vertex','time_period'])
        self.demandGas = df_temp['demand']

        # Initialise Data in sheet 'solar_generation'
        df_temp = dict_pd['solar_generation'].set_index(['vertex','time_period','scenario'])
        self.generationSolar = df_temp['generation']

        # Initialise Data in sheet 'wind_generation'
        df_temp = dict_pd['wind_generation'].set_index(['vertex','time_period','scenario'])
        self.generationWind = df_temp['generation']	
	
        # Initialise Data in sheet 'scalar_params'
        df_temp = dict_pd['scalar_params']
        self.conversionGasLiquid      = df_temp['unit_convertion_gas_liquid'].iloc[0]
        self.conversionElectricityGas = df_temp['unit_convertion_electricity_gas'].iloc[0]
        self.efficiencyElectrolysis   = df_temp['efficiency_electrolysis'].iloc[0]
        self.efficiencyLiquefaction   = df_temp['efficiency_liquefaction'].iloc[0]
        self.efficiencyGasification   = df_temp['efficiency_gasification'].iloc[0]
        self.maxLossLoadElectricity   = df_temp['max_electricity_loss_load_percentage'].iloc[0]
        self.maxLossLoadGas           = df_temp['max_gas_loss_load_percentage'].iloc[0]
        self.costStorageGas           = df_temp['operational_cost_gas_storage'].iloc[0]
        self.costStorageLiquid        = df_temp['operational_cost_liquid_storage'].iloc[0]
        
class ModelMOPTA(gp.Model):    
    def __init__(self, instance:InstanceMOPTA, **kwds):
        super().__init__(**kwds)
        self.__inst = instance
        self.__build_variables()
        self.__build_constraints()
        self.__build_objective()
        self.update()
    
    @property
    def inst(self):
        return self.__inst
    
    @property
    def buildNumSolar(self):
        return self.__buildNumSolar
    @property
    def buildNumWind(self):
        return self.__buildNumWind
    @property
    def buildNumStorageGas(self):
        return self.__buildNumStorageGas
    @property
    def buildNumStorageLiquid(self):
        return self.__buildNumStorageLiquid
    @property
    def flowElectricity(self):
        return self.__flowElectricity
    @property
    def flowGas(self):
        return self.__flowGas
    @property
    def flowLiquid(self):
        return self.__flowLiquid
    @property
    def lossLoadElectricity(self):
        return self.__lossLoadElectricity
    @property
    def lossLoadGas(self):
        return self.__lossLoadGas
    @property
    def generationRenewable(self):
        return self.__generationRenewable
    @property
    def spillRenewable(self):
        return self.__spillRenewable
    @property
    def storageGasSoc(self):
        return self.__storageGasSoc
    @property
    def storageGasCharge(self):
        return self.__storageGasCharge
    @property
    def storageGasDischarge(self):
        return self.__storageGasDischarge
    @property
    def storageLiquidSoc(self):
        return self.__storageLiquidSoc
    @property
    def storageLiquidCharge(self):
        return self.__storageLiquidCharge
    @property
    def storageLiquidDischarge(self):
        return self.__storageLiquidDischarge

    def __build_variables(self):
        # First Stage Decisions      
        self.__buildNumSolar = self.addVars(self.inst.SolarNodes, vtype=GRB.INTEGER)
        self.__buildNumWind  = self.addVars(self.inst.WindNodes, vtype=GRB.INTEGER)
        self.__buildNumStorageGas    = self.addVars(self.inst.ElectrolyzerNodes, vtype=GRB.INTEGER)
        self.__buildNumStorageLiquid = self.addVars(self.inst.TankNodes, vtype=GRB.INTEGER)
        
        # Flow Decisions
        self.__flowElectricity = self.addVars(self.inst.Nodes, self.inst.Nodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)
        self.__flowGas         = self.addVars(self.inst.Nodes, self.inst.Nodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)
        self.__flowLiquid      = self.addVars(self.inst.Nodes, self.inst.Nodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)

        self.__lossLoadElectricity = self.addVars(self.inst.LoadNodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)
        self.__lossLoadGas         = self.addVars(self.inst.IndustrialNodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)

        # Generation Decision
        self.__generationRenewable = self.addVars(self.inst.RenewableNodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)
        self.__spillRenewable      = self.addVars(self.inst.RenewableNodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)

        # Storage Decisions
        self.__storageGasSoc       = self.addVars(self.inst.ElectrolyzerNodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)
        self.__storageGasCharge    = self.addVars(self.inst.ElectrolyzerNodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)
        self.__storageGasDischarge = self.addVars(self.inst.ElectrolyzerNodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)

        self.__storageLiquidSoc       = self.addVars(self.inst.TankNodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)
        self.__storageLiquidCharge    = self.addVars(self.inst.TankNodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)
        self.__storageLiquidDischarge = self.addVars(self.inst.TankNodes, self.inst.TimePeriods, self.inst.Scenarios, vtype=GRB.CONTINUOUS)

    def __build_constraints(self):
        # First Stage Constraints
        self.addConstrs((cons_build_solar_bound(self, i) for i in self.inst.SolarNodes), name="CbuildSolarBound")
        self.addConstrs((cons_build_wind_bound(self, i) for i in self.inst.WindNodes), name="CbuildWindBound")

        # Flow Balance Constraints
        self.addConstrs((cons_flow_balance_loads(self, i, t, s) for i in self.inst.LoadNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CflowBalanceLoads")
        self.addConstrs((cons_flow_balance_gas_loads(self, i, t, s) for i in self.inst.IndustrialNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CflowBalanceGasLoads")

        self.addConstrs((cons_flow_balance_renewables(self, i, t, s) for i in self.inst.RenewableNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CflowBalanceRenewables")
        self.addConstrs((cons_renewable_generation_def(self, i, t, s) for i in self.inst.RenewableNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="renewableGenerationDef")
        
        self.addConstrs((cons_flow_balance_electrolyzers(self, i, t, s) for i in self.inst.ElectrolyzerNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CflowBalanceElectrolyzers")
        self.addConstrs((cons_flow_balance_tanks(self, i, t, s) for i in self.inst.TankNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CflowBalanceTanks")
        self.addConstrs((cons_flow_balance_fuelcells(self, i, t, s) for i in self.inst.FuelCellNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CflowBalanceFuelCells")
        
        # Battery Constraints
        self.addConstrs((cons_soc_update_storage_liquid(self, i, t, s) for i in self.inst.TankNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CstorageLiquidUpdate")
        self.addConstrs((cons_soc_update_storage_gas(self, i, t, s) for i in self.inst.ElectrolyzerNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CstorageGasUpdate")

        self.addConstrs((cons_max_capacity_storage_liquid(self, i, t, s) for i in self.inst.TankNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CmaxStorageLiquid")
        self.addConstrs((cons_max_capacity_storage_gas(self, i, t, s) for i in self.inst.ElectrolyzerNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CmaxStorageGas")

        self.addConstrs((cons_max_liquid_charge_bound(self, i, t, s) for i in self.inst.TankNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CmaxChargeLiquid")
        self.addConstrs((cons_max_liquid_discharge_bound(self, i, t, s) for i in self.inst.TankNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CmaxDischargeLiquid")
        self.addConstrs((cons_max_gas_charge_bound(self, i, t, s) for i in self.inst.ElectrolyzerNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CmaxChargeGas")
        self.addConstrs((cons_max_gas_discharge_bound(self, i, t, s) for i in self.inst.ElectrolyzerNodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CmaxDischargeGas")

        # Loss of Load Contraints
        self.addConstrs((cons_max_loss_load_electricity(self, s) for s in self.inst.Scenarios), name="CmaxLossLoadElectricity")
        self.addConstrs((cons_max_loss_load_gas(self, s) for s in self.inst.Scenarios), name="CmaxLossLoadGas")

        # Bound Contraints
        self.addConstrs((cons_max_flow_electricity(self, i, j, t, s) for i in self.inst.Nodes for j in self.inst.Nodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CmaxFlowElectricity")
        self.addConstrs((cons_max_flow_gas(self, i, j, t, s) for i in self.inst.Nodes for j in self.inst.Nodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CmaxFlowGas")
        self.addConstrs((cons_max_flow_liquid(self, i, j, t, s) for i in self.inst.Nodes for j in self.inst.Nodes for t in self.inst.TimePeriods for s in self.inst.Scenarios), name="CmaxFlowLiquid")

    def __build_objective(self):
        self.setObjective(obj_cost(self), GRB.MINIMIZE)

    def load_solution_inst(self):
        # Update solution loaded and optimality status parameters
        if (self.Status == GRB.OPTIMAL):
            self.inst.optimality_status = 'Optimal'
        elif (self.Status == GRB.INFEASIBLE):
            self.inst.optimality_status = 'Infeasible'
        elif (self.Status == GRB.UNBOUNDED):
            self.inst.optimality_status = 'Unbounded'
        else:
            self.inst.optimality_status = f'Termination Status {self.Status}'
        
        assert (hasattr(self.buildNumSolar[list(self.inst.SolarNodes)[0]], 'X')), f'Solutions do not exist, the model must be solved to optimality before.'
        self.inst.is_solution_loaded = True

        self.inst.buildNumSolar = pd.DataFrame.from_dict({index: var.X for index, var in self.buildNumSolar.items()}, orient='index', columns=['buildNumSolar'])
        self.inst.buildNumSolar.index.name = 'Solar Plant'
        self.inst.buildNumWind = pd.DataFrame.from_dict({index: var.X for index, var in self.buildNumWind.items()}, orient='index', columns=['buildNumWind'])
        self.inst.buildNumWind.index.name = 'Wind Plant'
        self.inst.buildNumStorageGas = pd.DataFrame.from_dict({index: var.X for index, var in self.buildNumStorageGas.items()}, orient='index', columns=['buildNumStorageGas'])
        self.inst.buildNumStorageGas.index.name = 'Electrolyzer'
        self.inst.buildNumStorageLiquid = pd.DataFrame.from_dict({index: var.X for index, var in self.buildNumStorageLiquid.items()}, orient='index', columns=['buildNumStorageLiquid'])
        self.inst.buildNumStorageLiquid.index.name = 'Hydrogen Tank'

        self.inst.flowElectricity = pd.DataFrame.from_dict({index: var.X for index, var in self.flowElectricity.items()}, orient='index', columns=['flowElectricity'])
        self.inst.flowElectricity.index = pd.MultiIndex.from_tuples(self.inst.flowElectricity.index, names=('Node', 'Node', 'Time Period', 'Scenario')) # Set MultiIndex
        self.inst.flowGas = pd.DataFrame.from_dict({index: var.X for index, var in self.flowGas.items()}, orient='index', columns=['flowGas'])
        self.inst.flowGas.index = pd.MultiIndex.from_tuples(self.inst.flowGas.index, names=('Node', 'Node', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.inst.flowLiquid = pd.DataFrame.from_dict({index: var.X for index, var in self.flowLiquid.items()}, orient='index', columns=['flowLiquid'])
        self.inst.flowLiquid.index = pd.MultiIndex.from_tuples(self.inst.flowLiquid.index, names=('Node', 'Node', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.inst.lossLoadElectricity = pd.DataFrame.from_dict({index: var.X for index, var in self.lossLoadElectricity.items()}, orient='index', columns=['lossLoadElectricity'])
        self.inst.lossLoadElectricity.index = pd.MultiIndex.from_tuples(self.inst.lossLoadElectricity.index, names=('Load Area', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.inst.lossLoadGas = pd.DataFrame.from_dict({index: var.X for index, var in self.lossLoadGas.items()}, orient='index', columns=['lossLoadGas'])
        self.inst.lossLoadGas.index = pd.MultiIndex.from_tuples(self.inst.lossLoadGas.index, names=('Industrial Area', 'Time Period', 'Scenario')) # Set MultiIndex 

        self.inst.generationRenewable = pd.DataFrame.from_dict({index: var.X for index, var in self.generationRenewable.items()}, orient='index', columns=['generationRenewable'])
        self.inst.generationRenewable.index = pd.MultiIndex.from_tuples(self.inst.generationRenewable.index, names=('Renewable Plant', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.inst.spillRenewable = pd.DataFrame.from_dict({index: var.X for index, var in self.spillRenewable.items()}, orient='index', columns=['spillRenewable'])
        self.inst.spillRenewable.index = pd.MultiIndex.from_tuples(self.inst.spillRenewable.index, names=('Renewable Plant', 'Time Period', 'Scenario')) # Set MultiIndex 
        
        self.inst.storageGasSoc = pd.DataFrame.from_dict({index: var.X for index, var in self.storageGasSoc.items()}, orient='index', columns=['storageGasSoc'])
        self.inst.storageGasSoc.index = pd.MultiIndex.from_tuples(self.inst.storageGasSoc.index, names=('Electrolyzer', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.inst.storageGasCharge = pd.DataFrame.from_dict({index: var.X for index, var in self.storageGasCharge.items()}, orient='index', columns=['storageGasCharge'])
        self.inst.storageGasCharge.index = pd.MultiIndex.from_tuples(self.inst.storageGasCharge.index, names=('Electrolyzer', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.inst.storageGasDischarge = pd.DataFrame.from_dict({index: var.X for index, var in self.storageGasDischarge.items()}, orient='index', columns=['storageGasDischarge'])
        self.inst.storageGasDischarge.index = pd.MultiIndex.from_tuples(self.inst.storageGasDischarge.index, names=('Electrolyzer', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.inst.storageLiquidSoc = pd.DataFrame.from_dict({index: var.X for index, var in self.storageLiquidSoc.items()}, orient='index', columns=['storageLiquidSoc'])
        self.inst.storageLiquidSoc.index = pd.MultiIndex.from_tuples(self.inst.storageLiquidSoc.index, names=('Hydrogen Tank', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.inst.storageLiquidCharge = pd.DataFrame.from_dict({index: var.X for index, var in self.storageLiquidCharge.items()}, orient='index', columns=['storageLiquidCharge'])
        self.inst.storageLiquidCharge.index = pd.MultiIndex.from_tuples(self.inst.storageLiquidCharge.index, names=('Hydrogen Tank', 'Time Period', 'Scenario')) # Set MultiIndex 
        self.inst.storageLiquidDischarge = pd.DataFrame.from_dict({index: var.X for index, var in self.storageLiquidDischarge.items()}, orient='index', columns=['storageLiquidDischarge'])
        self.inst.storageLiquidDischarge.index = pd.MultiIndex.from_tuples(self.inst.storageLiquidDischarge.index, names=('Hydrogen Tank', 'Time Period', 'Scenario')) # Set MultiIndex 


#------------------------------------------------------------------------------
# Auxiliary Functions to Define Constraints
#------------------------------------------------------------------------------

def cons_build_solar_bound(m:ModelMOPTA, i:int):
    return m.buildNumSolar[i] <= m.inst.capacitySolar[i]

def cons_build_wind_bound(m:ModelMOPTA, i:int):
    return m.buildNumWind[i] <= m.inst.capacityWind[i]

def cons_flow_balance_loads(m:ModelMOPTA, i:int, t:int, s:int):
    inflow = sum(m.flowElectricity[j,i,t,s] for j in m.inst.Nodes) + m.lossLoadElectricity[i,t,s] 
    outflow = sum(m.flowElectricity[i,j,t,s] for j in m.inst.Nodes) + m.inst.demandElectricity[i,t]
    return inflow == outflow

def cons_flow_balance_renewables(m:ModelMOPTA, i:int, t:int, s:int):
    inflow = sum(m.flowElectricity[j,i,t,s] for j in m.inst.Nodes) + m.generationRenewable[i,t,s] 
    outflow = sum(m.flowElectricity[i,j,t,s] for j in m.inst.Nodes) + m.spillRenewable[i,t,s]
    return inflow == outflow

def cons_renewable_generation_def(m:ModelMOPTA, i:int, t:int, s:int):
    if i in m.inst.SolarNodes:
        rhs = m.inst.generationSolar[i,t,s] * m.buildNumSolar[i]
    elif i in m.inst.WindNodes:
        rhs = m.inst.generationWind[i,t,s] * m.buildNumWind[i]
    else:
        rhs = 0
    return m.generationRenewable[i,t,s] == rhs

def cons_flow_balance_gas_loads(m:ModelMOPTA, i:int, t:int, s:int):
    inflow = sum(m.flowGas[j,i,t,s] for j in m.inst.Nodes) + m.lossLoadGas[i,t,s] 
    outflow = sum(m.flowGas[i,j,t,s] for j in m.inst.Nodes) + m.inst.demandGas[i,t]
    return inflow == outflow

def cons_flow_balance_electrolyzers(m:ModelMOPTA, i:int, t:int, s:int):
    electflow = sum(m.flowElectricity[j,i,t,s] for j in m.inst.Nodes)
    gasflow = m.inst.conversionElectricityGas * m.inst.efficiencyElectrolysis * (sum(m.flowGas[i,j,t,s] for j in m.inst.Nodes) + m.storageGasCharge[i,t,s] - m.storageGasDischarge[i,t,s])
    return electflow == gasflow

def cons_flow_balance_tanks(m:ModelMOPTA, i:int, t:int, s:int):
    inflow = sum(m.flowGas[j,i,t,s] for j in m.inst.Nodes)
    outflow = m.inst.conversionGasLiquid * m.inst.efficiencyLiquefaction * (sum(m.flowLiquid[i,j,t,s] for j in m.inst.Nodes) + m.storageLiquidCharge[i,t,s] - m.storageLiquidDischarge[i,t,s])
    return inflow == outflow

def cons_flow_balance_fuelcells(m:ModelMOPTA, i:int, t:int, s:int):
    inflow = m.inst.efficiencyGasification * (sum(m.flowGas[j,i,t,s] for j in m.inst.Nodes) + m.inst.conversionGasLiquid * sum(m.flowLiquid[j,i,t,s] for j in m.inst.Nodes))
    outflow = sum(m.flowGas[i,j,t,s] for j in m.inst.Nodes) + sum(m.flowElectricity[i,j,t,s] for j in m.inst.Nodes)/m.inst.conversionElectricityGas
    return inflow == outflow

def cons_soc_update_storage_liquid(m:ModelMOPTA, i:int, t:int, s:int):
    if t == min(m.inst.TimePeriods):
        t_final = max(m.inst.TimePeriods)
        charged = m.inst.effChargingStorageLiquid[i] * m.storageLiquidCharge[i,t_final,s]
        discharged = 1/m.inst.effDischargingStorageLiquid[i] * m.storageLiquidDischarge[i,t_final,s]
        return m.storageLiquidSoc[i,t,s] == (1 - m.inst.selfDischargeStorageLiquid[i]) * m.storageLiquidSoc[i,t_final,s] + charged - discharged
    else:
        charged = m.inst.effChargingStorageLiquid[i] * m.storageLiquidCharge[i,t-1,s]
        discharged = 1/m.inst.effDischargingStorageLiquid[i] * m.storageLiquidDischarge[i,t-1,s]
        return m.storageLiquidSoc[i,t,s] == (1 - m.inst.selfDischargeStorageLiquid[i]) * m.storageLiquidSoc[i,t-1,s] + charged - discharged

def cons_soc_update_storage_gas(m:ModelMOPTA, i:int, t:int, s:int):
    for d in m.inst.Days:
        if t == m.inst.startPeriodOfDay[d]:
            t_final = m.inst.endPeriodOfDay[d]
            charged = m.inst.effChargingStorageGas[i] * m.storageGasCharge[i,t_final,s]
            discharged = 1/m.inst.effDischargingStorageGas[i] * m.storageGasDischarge[i,t_final,s]
            return m.storageGasSoc[i,t,s] == (1 - m.inst.selfDischargeStorageGas[i]) * m.storageGasSoc[i,t_final,s] + charged - discharged
    
    charged = m.inst.effChargingStorageGas[i] * m.storageGasCharge[i,t-1,s]
    discharged = 1/m.inst.effDischargingStorageGas[i] * m.storageGasDischarge[i,t-1,s]
    return m.storageGasSoc[i,t,s] == (1 - m.inst.selfDischargeStorageGas[i]) * m.storageGasSoc[i,t-1,s] + charged - discharged

def cons_max_capacity_storage_liquid(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageLiquidSoc[i,t,s] <= m.inst.capacityTank[i] * m.buildNumStorageLiquid[i]

def cons_max_capacity_storage_gas(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageGasSoc[i,t,s] <= m.inst.capacityElectrolyzer[i] * m.buildNumStorageGas[i]

def cons_max_gas_charge_bound(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageGasCharge[i,t,s] <= m.inst.maxChargeElectrolyzer[i] * m.buildNumStorageGas[i]

def cons_max_gas_discharge_bound(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageGasDischarge[i,t,s] <= m.inst.maxChargeElectrolyzer[i] * m.buildNumStorageGas[i]

def cons_max_liquid_charge_bound(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageLiquidCharge[i,t,s] <= m.inst.maxChargeTank[i] * m.buildNumStorageLiquid[i]

def cons_max_liquid_discharge_bound(m:ModelMOPTA, i:int, t:int, s:int):
    return m.storageLiquidDischarge[i,t,s] <= m.inst.maxChargeTank[i] * m.buildNumStorageLiquid[i]

def cons_max_loss_load_electricity(m:ModelMOPTA, s:int):
    rhs = m.inst.maxLossLoadElectricity * sum(m.inst.demandElectricity[i,t] for i in m.inst.LoadNodes for t in m.inst.TimePeriods)
    return sum(m.lossLoadElectricity[i,t,s] for i in m.inst.LoadNodes for t in m.inst.TimePeriods) <= rhs

def cons_max_loss_load_gas(m:ModelMOPTA, s:int):
    rhs = m.inst.maxLossLoadGas * sum(m.inst.demandGas[i,t] for i in m.inst.IndustrialNodes for t in m.inst.TimePeriods)
    return sum(m.lossLoadGas[i,t,s] for i in m.inst.IndustrialNodes for t in m.inst.TimePeriods) <= rhs

def cons_max_flow_electricity(m:ModelMOPTA, i:int, j:int, t:int, s:int):
    if (i,j) in m.inst.capacityEdgeElectricity.index:
        return m.flowElectricity[i,j,t,s] <= m.inst.capacityEdgeElectricity[i,j]
    else:
        return m.flowElectricity[i,j,t,s] <= 0

def cons_max_flow_gas(m:ModelMOPTA, i:int, j:int, t:int, s:int):
    if (i,j) in m.inst.capacityEdgeGas.index:
        return m.flowGas[i,j,t,s] <= m.inst.capacityEdgeGas[i,j]
    else:
        return m.flowGas[i,j,t,s] <= 0

def cons_max_flow_liquid(m:ModelMOPTA, i:int, j:int, t:int, s:int):
    if (i,j) in m.inst.capacityEdgeLiquid.index:
        return m.flowLiquid[i,j,t,s] <= m.inst.capacityEdgeLiquid[i,j]
    else:
        return m.flowLiquid[i,j,t,s] <= 0

def obj_cost(m:ModelMOPTA):
    # Investement Costs
    cost_build_solar = sum(m.inst.costBuildSolar[i]*m.buildNumSolar[i] for i in m.inst.SolarNodes)
    cost_build_wind  = sum(m.inst.costBuildWind[i]*m.buildNumWind[i] for i in m.inst.WindNodes)

    cost_build_storage_gas = sum(m.inst.costBuildStorageGas[i]*m.buildNumStorageGas[i] for i in m.inst.ElectrolyzerNodes)
    cost_build_storage_liquid = sum(m.inst.costBuildStorageLiquid[i]*m.buildNumStorageLiquid[i] for i in m.inst.TankNodes)

    # Operational Costs
    cost_storage_gas = sum(m.inst.scenarioWeight[s] * (sum(m.inst.costStorageGas*m.storageGasSoc[i,t,s] for i in m.inst.ElectrolyzerNodes for t in m.inst.TimePeriods)) for s in m.inst.Scenarios)
    cost_storage_liquid = sum(m.inst.scenarioWeight[s] * (sum(m.inst.costStorageLiquid*m.storageLiquidSoc[i,t,s] for i in m.inst.TankNodes for t in m.inst.TimePeriods)) for s in m.inst.Scenarios)
    
    return cost_build_solar + cost_build_wind + cost_build_storage_gas + cost_build_storage_liquid + cost_storage_gas + cost_storage_liquid

#------------------------------------------------------------------------------
# Auxiliary Functions to Deal with Solutions
#------------------------------------------------------------------------------

def run_optimality_check(model:ModelMOPTA):
    if model.Status == GRB.OPTIMAL:
        print("Model is optimal")
        print(f"Optimal objective: {model.ObjVal:g}")
    else:
        print(f"Optimization ended with status {model.Status}")

# TODO fix run_economical_analysis() to take gp model 
def run_economical_analysis(model:pyo.ConcreteModel, ll_perc_lb:float, ll_perc_ub:float, ll_perc_step:float):
    assert ((ll_perc_lb>=0) & (ll_perc_lb <=1)), f"The parameter 'll_perc_lb'={ll_perc_lb} must be a percentage."
    assert ((ll_perc_ub>=0) & (ll_perc_ub <=1)), f"The parameter 'll_perc_ub'={ll_perc_ub} must be a percentage."
    assert ((ll_perc_step>=0) & (ll_perc_step <=1)), f"The parameter 'll_perc_step'={ll_perc_step} must be between 0 and 1."

    ll_perc_E = ll_perc_lb
    ll_perc_G = ll_perc_lb
    df_results = pd.DataFrame(columns=['ll_perc_E', 'll_perc_G', 'investment_solar','investment_wind',
                                       'investment_storage_gas','investment_storage_liquid',
                                       'investment_cost', 'operational_cost']
                              + [f"operational_cost_{s}" for s in model.Scenarios] 
                              + [f"ll_dual_E_{s}" for s in model.Scenarios]
                              + [f"ll_dual_G_{s}" for s in model.Scenarios])
    
    for ll_perc_E in np.arange(ll_perc_lb, ll_perc_ub+ll_perc_step, ll_perc_step):
        for ll_perc_G in np.arange(ll_perc_lb, ll_perc_ub+ll_perc_step, ll_perc_step):
            print(f"Elect = {ll_perc_E} | Gas = {ll_perc_G}")
            # Update Maximum Loss Load Parameter
            model.maxLossLoadElectricity = ll_perc_E
            model.maxLossLoadGas = ll_perc_G

            # Run MILP Model
            results = run_solve(model, warmstart=True)
            model = run_optimality_check(results, model)

            # Get optimal OPERATIONAL Costs
            cost_build_solar = sum(model.costBuildSolar[i]*pyo.value(model.buildNumSolar[i]) for i in model.SolarNodes)
            cost_build_wind  = sum(model.costBuildWind[i]*pyo.value(model.buildNumWind[i]) for i in model.WindNodes)
            cost_build_storage_gas = sum(model.costBuildStorageGas[i]*pyo.value(model.buildNumStorageGas[i]) for i in model.ElectrolyzerNodes)
            cost_build_storage_liquid = sum(model.costBuildStorageLiquid[i]*pyo.value(model.buildNumStorageLiquid[i]) for i in model.TankNodes)
            investment_cost = cost_build_solar + cost_build_wind + cost_build_storage_gas + cost_build_storage_liquid

            # Fix investement decision, relax integrality and re-solve LP
            LPmodel = fix_integer_variables(model)
        
            # Re-run model
            if (ll_perc_E == ll_perc_lb) and (ll_perc_G == ll_perc_lb):
                LPmodel.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT_EXPORT) #Needed to export dual values later
            results2 = run_solve(LPmodel, warmstart=True)
            LPmodel = run_optimality_check(results2, LPmodel)
            
            # Get optimal OPERATIONAL Costs
            cost_storage_gas = {s: (sum(LPmodel.costStorageGas * pyo.value(LPmodel.storageGasSoc[i,t,s])\
                                        for i in LPmodel.ElectrolyzerNodes for t in LPmodel.TimePeriods)) for s in LPmodel.Scenarios}
            cost_storage_liquid = {s: (sum(LPmodel.costStorageLiquid * pyo.value(LPmodel.storageLiquidSoc[i,t,s])\
                                        for i in LPmodel.TankNodes for t in LPmodel.TimePeriods)) for s in LPmodel.Scenarios}
            operarional_costs = {s: cost_storage_gas[s] + cost_storage_liquid[s] for s in LPmodel.Scenarios}

            # Compute Loss of Load Duals/Prices
            duals_E = {s: LPmodel.dual[LPmodel.CmaxLossLoadElectricity[s]] for s in LPmodel.Scenarios}
            duals_G = {s: LPmodel.dual[LPmodel.CmaxLossLoadGas[s]] for s in LPmodel.Scenarios}

            # Update dataframe of results
            new_row = {'ll_perc_E': ll_perc_E, 
                       'll_perc_G': ll_perc_G,
                       'investment_solar': cost_build_solar,
                       'investment_wind': cost_build_wind,
                       'investment_storage_gas': cost_build_storage_gas,
                       'investment_storage_liquid': cost_build_storage_liquid,
                       'investment_cost': investment_cost,
                       'operational_cost': sum(operarional_costs[s] for s in LPmodel.Scenarios)}
            for s in LPmodel.Scenarios:
                new_row[f"operational_cost_{s}"] = operarional_costs[s]
                new_row[f"ll_dual_E_{s}"] = duals_E[s]
                new_row[f"ll_dual_G_{s}"] = duals_G[s]

            df_results = pd.concat([df_results, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    return df_results

def plot_economical_analysis(data_filename:str, scenario:int, scenario_name:str, z_axis:str, fig_filename:str, num_tol:int=0.00001):
    assert z_axis in ['operational_cost', 'dual_E', 'dual_G'], f"z_axis argument must be one of ['operational_cost', 'dual_E', 'dual_G']"
    
    # Read data and save column names
    df = pd.read_csv(data_filename)
    x_name = 'll_perc_E'
    y_name = 'll_perc_G'
    df[x_name] = df[x_name] * 100
    df[y_name] = df[y_name] * 100

    if z_axis == 'operational_cost':
        z_name  = f'operational_cost_'+str(scenario)
        z_cmap  = 'RdYlGn_r'
        z_title = f'Operational Cost \n of Scenario {scenario_name}'
    elif z_axis == 'dual_E':
        z_name  = f'll_dual_E_'+str(scenario)
        z_cmap  = 'RdYlGn'
        z_title = f'Shadow Price of Lost Electricity Load \n under Scenario {scenario_name}'
    else: # z_axis == 'dual_G'
        z_name  = f'll_dual_G_'+str(scenario)
        z_cmap  = 'RdYlGn'
        z_title = f'Shadow Price of Lost Gas Load \n under Scenario {scenario_name}'

    # 2D-arrays from DataFrame
    x1 = np.linspace(df[x_name].min(), df[x_name].max(), len(df[x_name].unique()))
    y1 = np.linspace(df[y_name].min(), df[y_name].max(), len(df[y_name].unique()))
    x, y = np.meshgrid(x1, y1)

    n_row, n_col = x.shape
    z = np.absolute(np.array([[float(df.loc[(np.abs(df[x_name]-x[i,j])<num_tol) & (np.abs(df[y_name]-y[i,j])<num_tol), z_name])
                               for j in range(n_col)] for i in range(n_row)]))    
    # Set up axes and put data on the surface
    fig = plt.figure()
    axes = fig.add_subplot(projection='3d')
    axes.plot_surface(x, y, z, cmap=z_cmap)

    # Customize labels
    axes.set_xlabel('Electricity Loss of Load (%)')
    axes.set_ylabel('Gas Loss of Load (%)')
    axes.set_title(z_title)     

    plt.savefig(fig_filename, bbox_inches='tight', pad_inches=0.3)
    plt.close()

### END