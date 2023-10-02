#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Tue Sep 15, 2023

@author: Antoine Bernas, PhD. 

This script has been adapted from transfer_normative_models_online.py (author: Pieter Barkema, https://github.com/predictive-clinical-neuroscience/PCNportal/blob/main/server/transfer_normative_models_online.py)

The purpose of this script is to use the function normative.transfer in a automated way for the BLR model.
usage:

    python transfer_BLR_Smith.py BLR_Smithnetworks_22k_45sites my_rs_fMRI_session my_test.csv my_adapt.csv
"""


"""

Transfer learning script for warped BLR model  
The script prepares and preprocesses data


Parameters
----------
root_dir : string
    The (currently hardcoded) path to the main project directory.
model_name : string
    The normative model chosen by the user. Name contains algorithm, training sample, 
    n collection sites.
data_type : string
    The data type chosen by the user to do normative modelling with.
session_id : string
    Unique session ID chosen by the user (e.g. My_model_test_1)

Returns
-------
None. It produces modelling results, and save them in root_dir/session_id/

    """
    
import os, sys
import numpy as np
import pandas as pd
import pickle
import pcntoolkit as ptk
from pcntoolkit.util.utils import create_design_matrix

# Read in website input.
root_dir = "/opt/shared/"
model_name= sys.argv[1]
session_id = sys.argv[2] #
adapt_file = sys.argv[3]
test_file = sys.argv[4]
#alg = model_name.split("_")[0] - Not used so far
#email_address = sys.argv[6] - not used so far
model_info_path = os.path.join(root_dir, model_name)
model_path = os.path.join(root_dir, model_name, "Models/")

# Create session directory
session_path = os.path.join(root_dir, session_id) +"/"
output_path = os.path.join(session_path, 'Transfer/')
outputsuffix = '_transfer'  # suffix added to the output files from the transfer function

print(f'{session_path}')
if not os.path.isdir(session_path):
            os.mkdir(session_path) 

# Read date in Root directory (/opt/shared/)
df_te = pd.read_csv(os.path.join(root_dir, test_file))
df_ad = pd.read_csv(os.path.join(root_dir, adapt_file))

# Extract a list of unique site ids for test and adaptation.
site_names = 'site_ids.txt'
with open(os.path.join(model_info_path, site_names)) as f:
    site_ids_tr = f.read().splitlines()
site_ids_te =  sorted(set(df_te['site'].to_list()))

# Read in, prepare and save test brain features.
with open(os.path.join(model_info_path,'idp_ids.txt')) as f:
    idps = f.read().splitlines()

breakpoint()

#Site enumeration.
sites = np.unique(df_te['site'])
df_te['sitenum'] = np.nan
for i, s in enumerate(sites):
    df_te['sitenum'].loc[df_te['site'] == s] = int(i)
df_ad['sitenum'] = np.nan
for i, s in enumerate(sites):
    df_ad['sitenum'].loc[df_ad['site'] == s] = int(i)

breakpoint()

# Extract a list of unique site ids for test and adaptation.
site_names = 'site_ids.txt'
with open(os.path.join(model_info_path, site_names)) as f:
    site_ids_tr = f.read().splitlines()
site_ids_te =  sorted(set(df_te['site'].to_list()))

# which data columns do we wish to use as covariates? Note that 'sites' cov is added in the 'create_design_matrix' later on
cols_cov = ['age','sex','mean_FD']

# limits for cubic B-spline basis 
xmin = -5 
xmax = 110

# Absolute Z treshold above which a sample is considered to be an outlier (without fitting any model)
outlier_thresh = 7


# extract and save the response variables for the test set
with open(os.path.join(model_info_path,'idp_ids.txt')) as f:
    idps = f.read().splitlines()

#idp_ids = [ 'CortexVol', 'CerebralWhiteMatterVol', 'SubCortGrayVol']

# for idp_num, idp in enumerate(idp_ids): 
#     print('Running IDP', idp_num, idp, ':')
#     idp_dir = os.path.join(session_path, idp)
#     if not os.path.isdir(idp_dir):
#         os.mkdir(idp_dir)
#     breakpoint()



# write response test file (with all idps in model path)
y_te = df_te[df_te.columns.intersection(set(idps))].to_numpy(dtype=float)
#y_te = df_ad[idp].to_numpy()

# save the variables
resp_file_te = os.path.join(session_path, 'resp_te.txt') 
np.savetxt(resp_file_te, y_te)
    
# configure and save the design matrix
cov_file_te = os.path.join(session_path, 'cov_bspline_te.txt')
x_te = create_design_matrix(df_te[cols_cov], 
                            site_ids = df_te['site'],
                            all_sites = site_ids_tr,
                            basis = 'bspline', 
                            xmin = xmin, 
                            xmax = xmax)
np.savetxt(cov_file_te, x_te)

# check whether all sites in the test set are represented in the training set
if all(elem in site_ids_tr for elem in site_ids_te):
    print('All sites are present in the training data')
    
    # just make predictions
    yhat_te, s2_te, Z = ptk.normative.predict(cov_file_te, 
                                alg='blr', 
                                respfile=resp_file_te, 
                                model_path=model_path)
else:
    print('Some sites missing from the training data. Adapting model')
    
    # save the covariates for the adaptation data
    x_ad = create_design_matrix(df_ad[cols_cov], 
                                site_ids = df_ad['site'],
                                all_sites = site_ids_tr,
                                basis = 'bspline', 
                                xmin = xmin, 
                                xmax = xmax)
    cov_file_ad = os.path.join(session_path, 'cov_bspline_ad.txt')          
    np.savetxt(cov_file_ad, x_ad)
    
    # save the responses for the adaptation data
    resp_file_ad = os.path.join(session_path, 'resp_ad.txt')

    y_ad = df_ad[df_ad.columns.intersection(set(idps))].to_numpy(dtype=float)
    #y_ad = df_ad[idp].to_numpy()
    np.savetxt(resp_file_ad, y_ad)
    
    # save the site ids for the adaptation data
    sitenum_file_ad = os.path.join(session_path, 'sitenum_ad.txt') 
    site_num_ad = df_ad['sitenum'].to_numpy(dtype=int)
    np.savetxt(sitenum_file_ad, site_num_ad)
    
    # save the site ids for the test data 
    sitenum_file_te = os.path.join(session_path, 'sitenum_te.txt')
    site_num_te = df_te['sitenum'].to_numpy(dtype=int)
    np.savetxt(sitenum_file_te, site_num_te)

    # breakpoint()
    breakpoint()
    # yhat_te, s2_te, Z = ptk.normative.predict(covfile = cov_file_te,
    #                             alg = 'blr', 
    #                             respfile = resp_file_te, 
    #                             model_path = model_path,
    #                             inputsuffix = 'fit',
    #                             outputsuffix = '_transfer',
    #                             adaptrespfile = resp_file_ad,
    #                             adaptcovfile = cov_file_ad,
    #                             adaptvargroupfile = sitenum_file_ad,
    #                             testvargroupfile = sitenum_file_te,
    #                             output_path = output_path,
    #                             savemodel = True)
    
    yhat_te, s2_te, Z = ptk.normative.transfer(cov_file_ad, 
                            resp_file_ad,
                            testcov = cov_file_te,
                            testresp = resp_file_te,
                            alg = 'blr', 
                            model_path = model_path,
                            trbefile = sitenum_file_ad,
                            tsbefile = sitenum_file_te,
                            inputsuffix = '_fit',
                            outputsuffix = '_transfer',
                            savemodel = True,
                            output_path = output_path)
    
    
    # test estimate model with test data
    #yhat_te, s2_te, nm, Z, metrics_te = ptk.normative.estimate(cov_file_te, resp_file_te, alg = 'blr', cvfolds = 3, outputsuffix = '_mytest')