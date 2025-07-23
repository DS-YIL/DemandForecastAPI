import pandas as pd
import numpy as np
import itertools
import os
import re


def code_break_explosion(code, qty, week=None):
    def eliminate(i, column_names, d1):
        # Individual characters in model code
        d1 = d1.loc[d1.loc[:, column_names[i]].str.contains(model_name[i], na=True)]
        return d1

    def and_eliminate(and_code, d1):
        d1 = d1.loc[d1['OPTION:AND'].isin(and_code)]
        return d1

    def or_eliminate(or_code, d1):
        pattern = '|'.join(or_code)
        if pattern:
            d1 = d1.loc[d1.loc[:, 'OPTION:OR'].str.contains(pattern, na=True)]
        else:
            d1 = d1[d1['OPTION:OR'].isnull()]
        return d1

    def not_eliminate(not_code, d1):
        pattern = '|'.join(not_code)
        d1 = d1.loc[~d1.loc[:, 'OPTION:NOT'].str.contains(pattern, na=False)]
        return d1

    def remove_duplicate_options(cpa_string):
        """
        Removes duplicate '/option' segments from the CPA string.
        """
        parts = cpa_string.split('/')
        deduped = []
        seen = set()

        for part in parts:
            if part not in seen:
                deduped.append(part)
                seen.add(part)

        return '/'.join(deduped)

    def process_option_codes(option_code, app_option, cpa):
        """
        Process and append option codes to CPA string based on app_option and rules.
        Ensures that if K1 is the last prefix, CPA remains in the standard format.
        """
        # Special rule: If K1 is the last prefix, return CPA in standard format
        if 'K1' in option_code:
            return cpa  # Return CPA as it is without appending additional suffixes

        # Handle other K rules (e.g., K2, K3, K6)
        if any(k in option_code for k in ['K2', 'K3', 'K6']):
            cpa += "/K3"
            option_code = [opt for opt in option_code if opt not in ['K2', 'K3', 'K6']]

        # Append valid options from app_option
        for opt in option_code:
            if opt in app_option:
                cpa += "/" + opt
            if opt == 'Z':
                cpa += "/Z"

        return cpa

    def cpa_code(st_code, option_code, model_name, app_option, cpa):
        """
        Generates CPA code based on the given rules for model_name and option_code.
        """
        # Exotic rule: Check the 2nd and 3rd characters of model_name
        if model_name[1] in ['F', 'L', 'Z'] or model_name[2] in ['H', 'M', 'T', 'A', 'D', 'B', 'W']:
            cpa += model_name[1] + model_name[2] + model_name[3] + model_name[4] + '-' + model_name[5] + 'NNNN'
            # Handle MH1 special case
            if 'MH1' in option_code:
                option_code = [opt for opt in option_code if opt != 'MH1']
                cpa += "/MG1"

            for k in ['K1', 'K2', 'K3', 'K5', 'K6']:
                if k in option_code:
                    cpa += "/" + k

            if 'MG1' in option_code and 'MH1' in option_code:
                cpa += "/MG1"

            # Append valid options from app_option
            for opt in option_code:
                if opt in app_option:
                    cpa += "/" + opt
                if opt == 'Z':
                    cpa += "/Z"

        # Non-exotic rule
        else:
            if model_name[1] + model_name[2] in st_code:
                suffix_map = {('M', 'L'): 'MS', ('H', 'L'): 'HS', ('V', 'L'): 'VS', ('A', 'L'): 'AS', ('B', 'L'): 'BS'}
                cpa += suffix_map.get((model_name[1], model_name[2]), model_name[1] + model_name[2]) + "NN-NNNNN"

                # Special rule for K1 as the last prefix
                if option_code and option_code[-1] == 'K1':
                    # Standard format: Remove prefixes or suffixes
                    print(model_code)
                    cpa = "CPA" + model_code[3:6] + "Y-N" + model_name[1:5] + "-" + model_name[5] + "NNNN"
                    return cpa

                if 'K1' in option_code or 'K5' in option_code:
                    option_code = [opt for opt in option_code if not opt.startswith('K')]

                if 'MG1' in option_code:
                    option_code.remove('MG1')

                if 'MH1' in option_code:
                    option_code.remove('MH1')

                # for adding K3 and Z option code
                cpa = process_option_codes(option_code, app_option, cpa)

            # if not in
            else:
                cpa += model_name[1] + model_name[2]
                cpa += '0' if model_name[3] in ['0', '1', '2'] else '5'
                cpa += model_name[4] + '-' + model_name[5] + 'NNNN'

                if option_code:
                    if model_name[2] == 'S' and model_name[1] in ['F', 'L']:
                        if 'MH1' in option_code:
                            option_code = [opt if opt != 'MH1' else 'MG1' for opt in option_code]

                    if 'HD' in option_code:
                        cpa = "CPA" + model_name[3:6] + "Y-N" + model_name[9:15] + "NNNN/HD"
                        option_code.remove('HD')

                    if 'MG1' in option_code:
                        option_code.remove('MG1')

                    if 'MH1' in option_code:
                        option_code.remove('MH1')

                    # for adding K3 and Z option code
                    cpa = process_option_codes(option_code, app_option, cpa)

        # Remove duplicates before returning
        return remove_duplicate_options(cpa)

    # main logic is here.
    model_name = code
    model_code = model_name[0:7]

    if (model_code == 'EJA530E'):
        model_name = model_name[8:12] + model_name[15:19]
        dataset = pd.read_csv(os.path.abspath('static/final530e.csv'))
        options = pd.read_csv(os.path.abspath('static/option530.csv'))  # Upload separate options file

    else:
        model_name = model_name[8:13] + model_name[14:19]
        dataset = pd.read_csv(os.path.abspath('static/final110e430e.csv'))
        options = pd.read_csv(os.path.abspath('static/option110.csv'))

    dataset = dataset.loc[dataset['SC'] != 1.0]
    pattern = [model_code, 'EJA530?']
    pattern = '|'.join(pattern)
    d1 = dataset.loc[dataset.loc[:, 'MODEL CODE'].str.contains(pattern, na=True)]

    if model_code == 'EJA530E':
        column_names = ['OUTPUT', 'SPAN', 'MATERIAL', 'P-CONNECT', 'HOUSING', 'E-CONNECT', 'INDICATOR', 'BRACKET']
    else:
        column_names = ['OUTPUT', 'SPAN', 'MATERIAL', 'P-CONNECT', 'BOLT-NUT', 'INSTALL', 'HOUSING', 'E-CONNECT',
                        'INDICATOR', 'BRACKET']

    # Iterating through the list of columns
    for i in range(len(column_names)):
        d1 = eliminate(i, column_names, d1)
    option_code = code[20:]
    temp = option_code.split('/')
    for i in list(set(temp).intersection(list(options['S/W Options']))):
        temp.remove(i)

    # Eliminating
    orr = [i for i in (list(options['OR'])) if i == i]
    or_code = list(set(temp).intersection(orr))
    andd = [i for i in (list(options['AND'])) if i == i]
    and_code = list(set(temp).intersection(andd))

    # Checking permutations of AND codes
    comb = [','.join(i) for i in itertools.permutations(and_code, r=2)]
    comb = list(set(comb).intersection(andd))  # List of valid combinations (EX: N1,GS)
    temp = list()
    for i in and_code:
        for j in comb:
            if re.search(i, j):
                temp.append(i)  # Making a list of and codes
    and_code = list(set(and_code) - set(temp)) + comb  # EX: list = 'X2','PR' + 'N1,GS'

    d1 = or_eliminate(or_code, d1)
    and_code.append(np.nan)
    d1 = and_eliminate(and_code, d1)
    del and_code[-1]
    opt_code = or_code + and_code
    if opt_code:
        if 'N4' in opt_code:
            opt_code.remove('N4')
        d1 = not_eliminate(opt_code, d1)

    # CPA Login start.
    option_code = option_code.split('/')
    cpa = "CPA" + model_code[3:6] + "Y-N"

    if model_code[3:6] == '110':
        st_code = ['MS', 'HS', 'VS', 'ML', 'HL', 'VL']
        app_option = ['K3', 'U1', 'HD', 'GS', 'N1', 'N2', 'N3', 'A1', 'A2', 'MG1', 'MH1']
        cpa = cpa_code(st_code, option_code, model_name, app_option, cpa)  # calling cpa_code

    elif model_code[3:6] == '430':
        st_code = ['AS', 'HS', 'BS', 'AL', 'HL', 'BL']
        app_option = ['K1', 'A1', 'A2', 'U1', 'GS', 'N1', 'N2', 'N3', 'MG1', 'MH1']
        cpa = cpa_code(st_code, option_code, model_name, app_option, cpa)  # calling cpa_code

    else:  # For 530E
        cpa = cpa + code[9:15] + "NNNN"
        app_option = ['K1', 'A1', 'A2', 'HG', 'MG1', 'MH1','HG']
        cpa = process_option_codes(option_code, app_option, cpa)

    # Final dataset adjustments
    d1 = d1.loc[d1['QTY'] != 0]
    unwanted = pd.read_csv((os.path.abspath('static/unwanted.csv')))
    unwanted_list = unwanted["PART NO."].tolist()
    pattern = '|'.join(unwanted_list)
    d1 = d1.loc[~d1.loc[:, 'PART NO.'].str.contains(pattern)]
    d1 = d1[["PART NO.", "PART NAME", "QTY"]]
    d1['Week'] = week
    d1 = d1.append({'PART NO.': cpa, 'PART NAME': 'CPA', 'QTY': 1.0, 'Week': week}, ignore_index=True)
    d1['QTY'] = d1['QTY'] * int(qty)
    return d1