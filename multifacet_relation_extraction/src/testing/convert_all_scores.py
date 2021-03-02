import os
import sys

in_dir = sys.argv[1]
out_dir = sys.argv[2]
model = sys.argv[3]

input_folder = os.path.join(os.getcwd(), 'output')
output_folder = os.path.join(os.getcwd(), 'results')

print('InDir: %s, OutDir: %s' % (in_dir, out_dir))
print('Current dir: %s' % os.getcwd())

update_list = ['upd', 'no_upd']
score_list = ['cos', 'kmeans_p2r', 'kmeans_r2p', 'kmeans_avg', 'SC_r2p', 'SC_p2r', 'SC_avg']
basis_list = ['b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b11']
epochs = [15, 20, 25, 30, 50]
year_list = ['2012', '2013', '2014']

ignored = 0

for basis in basis_list:
    for ep in epochs:
        basis_name = "{}ep{}".format(basis, ep)        
        #for update_name in update_list:
        for year_name in year_list:            
            in_file_rel_path = os.path.join(basis_name, "full_sentence_candidates_{}_scored".format( year_name))                
            input_file_name = os.path.join(input_folder, in_dir, model, in_file_rel_path)
            if not os.path.exists(input_file_name):
                ignored += 1
                continue
            print(in_file_rel_path)
            for score_idx, score_name in enumerate(score_list):
                score_field = str(score_idx + 10)
                out_file_rel_path = os.path.join("{}_{}".format(basis_name, score_name), "{}_scored".format(year_name))
                output_file_name = os.path.join(output_folder, out_dir, out_file_rel_path)                
                print("\t{}".format(out_file_rel_path))
                command = 'awk -F $\'\\t\' \'{print $1"\\t"$2"\\t"$3"\\t"$4"\\t0\\t0\\t0\\t0\\t"$' +score_field+ '}\' ' + input_file_name + ' > ' + output_file_name
                #print(command)
                os.makedirs(os.path.join(output_folder, out_dir, "{}_{}".format(basis_name, score_name)), exist_ok=True)                    
                os.system(command)                

total = len(basis_list)*len(epochs)*len(year_list)
print("{} input files converted for {}.".format(total-ignored, in_dir))

