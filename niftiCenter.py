def dot_product(v1, v2):
    return [a*b for (a,b) in zip(v1, v2)]


def centered_origin(hdr_in):

    hdr_out= hdr_in.copy()

    spc_dirs= hdr_in.get_sform()[0:3,0:3]

    new_origin = []
    for dir in spc_dirs:
        new_size= [(x-1)/2  for x in hdr_in['dim'][1:4]]

        dot_prod= dot_product(dir,new_size)
        abs_dot_prod= [abs(x) for x in dot_prod]

        max_elm= abs_dot_prod.index(max(abs_dot_prod))
        new_origin.append(-dot_prod[max_elm])


    hdr_out['qoffset_x'], hdr_out['qoffset_y'], hdr_out['qoffset_z']= new_origin
    hdr_out['srow_x'][3], hdr_out['srow_y'][3], hdr_out['srow_z'][3]= new_origin

    # save_image(mri_in.get_data(), hdr_out, out_prefix)

    return hdr_out