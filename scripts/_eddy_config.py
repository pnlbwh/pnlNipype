def obtain_fsl_eddy_params(fileName):

    topup_params=[]
    applytopup_params=[]
    eddy_openmp_params=[]

    # read the eddy configuration file:
    with open(fileName) as f:
        content= f.read().split('\n')
        for line in content:

            if '$ topup:' in line:
                topup_params= line.split(':')[1]

            elif '$ applytopup:' in line:
                applytopup_params= line.split(':')[1]

            elif '$ eddy_openmp:' in line:
                eddy_openmp_params= line.split(':')[1]


    return (topup_params, applytopup_params, eddy_openmp_params)
