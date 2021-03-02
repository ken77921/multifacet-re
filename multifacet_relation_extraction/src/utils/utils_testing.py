import numpy as np
import torch
import torch.utils.data
from scipy.spatial import distance

from utils.utils import str2bool
import utils.nsd_loss as nsd_loss

# sys.path.insert(0, sys.path[0]+'/testing/sim')
import math
from tqdm import tqdm


def add_model_arguments(parser):
    # embeddings
    # source embedding (pattern/relation word embedding)
    parser.add_argument('--source_emsize', type=int, default=0,
                        help='size of word embeddings')
    parser.add_argument('--source_emb_file', type=str, default='source_emb.pt',
                        help='path to the file of a word embedding file')

    # target embedding
    parser.add_argument('--target_emsize', type=int, default=0,
                        help='size of entity pair embeddings')
    parser.add_argument('--target_emb_file', type=str, default='target_emb.pt',
                        help='Location of the target embedding file')
    ###encoder
    # both
    parser.add_argument('--en_model', type=str, default='LSTM',
                    help='type of encoder model (LSTM, LSTM+TRANS, TRANS+LSTM, TRANS)')
    parser.add_argument('--dropouti', type=float, default=0.0,
                        help='dropout for input embedding layers (0 = no dropout)')
    parser.add_argument('--dropoute', type=float, default=0.0,
                        help='dropout to remove words from embedding layer (0 = no dropout)')
    parser.add_argument('--dropout', type=float, default=0.0,
                        help='dropout applied to the output layer (0 = no dropout) in case of LSTM, dropouts for transformer encoder in case of TRANS')
    #LSTM only
    parser.add_argument('--nhid', type=int, default=600,
                        help='number of hidden units per layer in LSTM')
    parser.add_argument('--nlayers', type=int, default=1,
                        help='number of layers')
    #TRANS only
    parser.add_argument('--encode_trans_layers', type=int, default=5,
                        help='How many layers we have in transformer. Do not have effect if de_model is LSTM')
    parser.add_argument('--trans_nhid', type=int, default=-1,
                        help='number of hidden units per layer in transformer')
    ###decoder
    #both
    parser.add_argument('--de_model', type=str, default='LSTM',
                        help='type of decoder model (LSTM, LSTM+TRANS, TRANS+LSTM, TRANS)')
    parser.add_argument('--de_coeff_model', type=str, default='LSTM',
                        help='type of decoder model to predict coefficients (LSTM, TRANS)')
    parser.add_argument('--n_basis', type=int, default=3,
                        help='number of basis we want to predict for sentence patterns')
    parser.add_argument('--n_basis_kb', type=int, default=-1,
                        help='number of basis we want to predict for kb relations')
    #parser.add_argument('--linear_mapping_dim', type=int, default=0,
    #                    help='map the input embedding by linear transformation')
    parser.add_argument('--positional_option', type=str, default='linear',
                        help='options of encode positional embedding into models (linear, cat, add)')
    parser.add_argument('--dropoutp', type=float, default=0.0,
                        help='dropout of positional embedding or input embedding after linear transformation (when linear_mapping_dim != 0)')
    #LSTM only
    parser.add_argument('--nhidlast2', type=int, default=-1,
                        help='hidden embedding size of the second LSTM')
    parser.add_argument('--dropout_prob_lstm', type=float, default=0,
                        help='LSTM decoder dropout')
    parser.add_argument('--nlayers_dec', type=int, default=1,
                        help='number of layers of the second LSTM')

    #TRANS only
    parser.add_argument('--trans_layers', type=int, default=5,
                        help='How many layers we have in transformer. Do not have effect if de_model is LSTM')
    parser.add_argument('--de_en_connection', type=str2bool, nargs='?', default=True, 
                        help='If True, using Transformer decoder in our decoder. Otherwise, using Transformer encoder')
    parser.add_argument('--dropout_prob_trans', type=float, default=0.0,
                        help='hidden_dropout_prob and attention_probs_dropout_prob in Transformer')


def predict_batch_simple(feature, parallel_encoder, parallel_decoder, normalize=True):
    output_emb_last, output_emb = parallel_encoder(feature)
    basis_pred, coeff_pred =  parallel_decoder(output_emb_last, output_emb, predict_coeff_sum = True)
    if normalize:
        basis_norm_pred = basis_pred / (0.000000000001 + basis_pred.norm(dim = 2, keepdim=True) )
    else:
        basis_norm_pred = basis_pred
    return coeff_pred, basis_norm_pred, output_emb_last, output_emb
    

def predict_batch(feature, parallel_encoder, parallel_decoder, word_norm_emb, target_norm_emb, n_basis, n_basis_kb, top_k, kb_marker=None, num_basis=None):
    normalize = (kb_marker is None and num_basis is None)
    # normalize = True
    coeff_pred, basis_pred, output_emb_last, output_emb = predict_batch_simple(feature, parallel_encoder, parallel_decoder, normalize)
    if not normalize:
        max_basis = max(n_basis, n_basis_kb)
        device = basis_pred.device
        n_batch = feature.size(0)
        if num_basis is not None and len(num_basis) != 0:
            # Add 1 to every element to avoid 0 basis
            num_basis = num_basis + 1
            # Make sure pattern basis and kb basis are clamped to the maximum values provided
            num_basis = torch.where(kb_marker, num_basis.clamp(max=n_basis_kb), num_basis.clamp(max=n_basis))
            # Create the mask: (N, T)
            mask = (torch.arange(max_basis).expand(n_batch, -1).to(dtype=num_basis.dtype,
                                                                   device=num_basis.device) < num_basis.view(-1, 1)) \
                .to(dtype=num_basis.dtype, device=num_basis.device)
        elif kb_marker is not None and len(kb_marker) != 0:
            pass
            mask = torch.where(kb_marker.unsqueeze(-1),
                               (torch.arange(max_basis) < n_basis_kb).to(dtype=torch.long, device=device),
                               (torch.arange(max_basis) < n_basis).to(dtype=torch.long, device=device))
        mask = mask.unsqueeze(-1)
        #basis_pred = mask.to(device) * basis_pred
        basis_norm_pred = basis_pred / (0.000000000001 + basis_pred.norm(dim = 2, keepdim=True) )
    else:
        mask = torch.ones(basis_pred.shape[:-1]).to(device=basis_pred.device).unsqueeze(-1)
        basis_norm_pred = basis_pred

    coeff_sum = coeff_pred.cpu().numpy()
    coeff_sum_diff = coeff_pred[:,:,0] - coeff_pred[:,:,1]
    coeff_sum_diff_pos = coeff_sum_diff.clamp(min = 0)
    coeff_sum_diff_cpu = coeff_sum_diff.cpu().numpy()
    coeff_order = np.argsort(coeff_sum_diff_cpu, axis = 1)
    coeff_order = np.flip( coeff_order, axis = 1 )

    basis_norm_pred = basis_norm_pred.permute(0,2,1)
    #basis_norm_pred should have dimension (n_batch, emb_size, n_basis)
    #word_norm_emb should have dimension (ntokens, emb_size)
    sim_pairwise = torch.matmul(target_norm_emb.unsqueeze(dim = 0), basis_norm_pred) # * mask.permute(0, 2, 1)
    #print(sim_pairwise.size())
    #sim_pairwise should have dimension (n_batch, ntokens, emb_size)
    top_value, top_index = torch.topk(sim_pairwise, top_k, dim=1, sorted=True)
    
    word_emb_input = word_norm_emb[feature,:]

    batch_sz = basis_norm_pred.size(0)
    num_basis = basis_norm_pred.size(-1)
    seq_len = word_emb_input.size(1)
    word_basis_sim = torch.ones(batch_sz, seq_len, num_basis).to(basis_norm_pred.device)
    word_basis_sim_pos = word_basis_sim.clamp(min = 0)

    bsz, max_sent_len, emb_size = output_emb.size()

    avg_out_emb = torch.empty(bsz, emb_size)
    word_imp_sim = []
    word_imp_sim_coeff = []
    word_imp_coeff = []
    for i in range(bsz):
        sent_len = (feature[i,:] != 0).sum()
        avg_out_emb[i,:] = output_emb[i,-sent_len:,:].mean(dim = 0)
        topic_weights = word_basis_sim_pos[i, -sent_len:, :]

        topic_weights_sum = topic_weights.sum(dim = 1)

        weights_nonzeros = topic_weights_sum.nonzero()
        weights_nonzeros_size = weights_nonzeros.size()
        if len(weights_nonzeros_size) == 2 and weights_nonzeros_size[1] == 1:
            weights_nonzeros = weights_nonzeros.squeeze(dim = 1)

        topic_weights_norm = topic_weights.clone()

        if weights_nonzeros.nelement() > 0:
            topic_weights_norm[weights_nonzeros,:] = topic_weights[weights_nonzeros,:] / topic_weights_sum[weights_nonzeros].unsqueeze(dim = 1)

        word_importnace_sim = topic_weights.sum(dim = 1).tolist()
        word_importnace_sim_coeff = (topic_weights*coeff_sum_diff_pos[i,:].unsqueeze(dim = 0) ).sum(dim = 1).tolist()
        word_importnace_coeff = (topic_weights_norm*coeff_sum_diff_pos[i,:]).sum(dim = 1).tolist()
        word_imp_sim.append(word_importnace_sim)
        word_imp_sim_coeff.append(word_importnace_sim_coeff)
        word_imp_coeff.append(word_importnace_coeff)

    basis_norm_pred = basis_norm_pred.permute(0, 2, 1) * mask
    pred_mean = basis_norm_pred.sum(dim=1, keepdim=True) / torch.sum(mask, dim=1, keepdim=True).to(device=basis_norm_pred.device)
    # print(mask.shape, basis_norm_pred.shape)
    variance = torch.sum(((basis_norm_pred - pred_mean) * mask).norm(dim=2), dim=1) / torch.sum(mask.squeeze(-1), dim=1)
    return basis_norm_pred, coeff_order, coeff_sum, top_value, top_index, output_emb_last, avg_out_emb, word_imp_sim,  word_imp_sim_coeff, word_imp_coeff, variance

def convert_feature_to_text(feature, idx2word_freq):
    feature_list = feature.tolist()
    feature_text = []
    for i in range(feature.size(0)):
        current_sent = []
        for w_ind in feature_list[i]:
            if w_ind != 0:
                w = idx2word_freq[w_ind][0]
                current_sent.append(w)
        feature_text.append(current_sent)
    return feature_text

def print_basis_text(feature, idx2word_freq, target_idx2word_freq, entpair_vocab_map, coeff_order, coeff_sum, top_value, top_index, i_batch, outf, n_basis, n_basis_kb, kb_marker=None, freebase_map=None, freq_threshold=0):
    if kb_marker is None:
        n_basis = coeff_order.shape[1]
    top_k = top_index.size(1)
    feature_text = convert_feature_to_text(feature, idx2word_freq)
    to_print = []
    for i_sent in range(len(feature_text)):
        current = {}
        current['pattern'] = ' '.join(feature_text[i_sent]);
        current['entity-pairs'] = []

        if kb_marker is None:
            valid_basis = n_basis
        else:
            valid_basis = n_basis_kb if kb_marker[i_sent] else n_basis

        for j in range(valid_basis):
            curbasis = []
            curbasis.append("Basis {}: ".format(j+1))
            org_ind = coeff_order[i_sent, j]
            count = 0
            for k in range(top_k):
                entpair = target_idx2word_freq[top_index[i_sent,k,org_ind].item()]
                if entpair[1] < freq_threshold: continue
                word_nn = entpair_vocab_map[entpair[0]]
                word_nn = "\t".join(list(map(lambda entity: freebase_map[entity] if freebase_map is not None and entity in freebase_map else entity, word_nn.split("\t"))))
                curbasis.append(word_nn+' {:5.3f}'.format(top_value[i_sent,k,org_ind].item()))
                count += 1
                if count == 5: break
            current['entity-pairs'].append(curbasis)
        to_print.append(current)
    return to_print


def visualize_topics_val(dataloader, parallel_encoder, parallel_decoder, word_norm_emb, idx2word_freq, target_norm_emb, target_idx2word_freq, entpair_vocab_map, outf, n_basis, n_basis_kb, max_batch_num, freebase_map, freq_threshold, top_k):
    to_print = []
    variances = []
    with torch.no_grad():
        for i_batch, sample_batched in tqdm(enumerate(dataloader), total=len(dataloader)):
            feature, target, kb_marker, num_basis = sample_batched

            basis_norm_pred, coeff_order, coeff_sum, top_value, top_index, encoded_emb, avg_encoded_emb, word_imp_sim, word_imp_sim_coeff, word_imp_coeff, variance = predict_batch(feature, parallel_encoder, parallel_decoder, word_norm_emb, target_norm_emb, n_basis, n_basis_kb, top_k, kb_marker, num_basis)
            variances.extend(variance.cpu().tolist())
            batch_to_print = print_basis_text(feature, idx2word_freq, target_idx2word_freq, entpair_vocab_map, coeff_order, coeff_sum, top_value, top_index, i_batch, outf, n_basis, n_basis_kb, kb_marker, freebase_map, freq_threshold)
            to_print.extend(batch_to_print)
            if i_batch >= max_batch_num: break
    
    sorted_variances_idx = np.argsort(-np.array(variances))
    for idx in sorted_variances_idx:
        outf.write(to_print[idx]['pattern'] + '\n')
        for basis_to_print in to_print[idx]['entity-pairs']:
            outf.write(' '.join(basis_to_print) + '\n')
        outf.write('\n')

class Set2SetDataset(torch.utils.data.Dataset):

    def __init__(self, source, source_w, source_sent_emb, source_avg_word_emb, target, target_w, target_sent_emb, target_avg_word_emb):
        self.source = source
        self.source_w = source_w
        self.source_sent_emb = source_sent_emb
        self.source_avg_word_emb = source_avg_word_emb
        self.target = target
        self.target_w = target_w
        self.target_sent_emb = target_sent_emb
        self.target_avg_word_emb = target_avg_word_emb

    def __len__(self):
        return self.source.size(0)

    def __getitem__(self, idx):
        source = self.source[idx, :, :]
        source_w = self.source_w[idx, :]
        source_sent_emb = self.source_sent_emb[idx, :]
        source_avg_word_emb = self.source_avg_word_emb[idx, :]
        target = self.target[idx, :, :]
        target_w = self.target_w[idx, :]
        target_sent_emb = self.target_sent_emb[idx, :]
        target_avg_word_emb = self.target_avg_word_emb[idx, :]
        return [source, source_w, source_sent_emb, source_avg_word_emb, target, target_w, target_sent_emb, target_avg_word_emb, idx]

def compute_freq_prob(word_d2_idx_freq):
    all_idx, all_freq= list( zip(*word_d2_idx_freq.values()) )
    freq_sum = float(sum(all_freq))
    for w in word_d2_idx_freq:
        idx, freq = word_d2_idx_freq[w]
        word_d2_idx_freq[w].append(freq/freq_sum)

def safe_cosine_sim(emb_1, emb_2):
    dist = distance.cosine(emb_1, emb_2)
    if math.isnan(dist):
        return 0
    else:
        return 1 - dist

def compute_AP_best_F1_acc(score_list, gt_list, correct_label = 1):
    sorted_idx = np.argsort(score_list)
    sorted_idx = sorted_idx.tolist()[::-1]
    total_correct = sum([1 if x == correct_label else 0 for x in  gt_list ])
    correct_count = 0
    total_count = 0
    precision_list = []
    F1_list = []
    acc_list = []
    false_neg_num = total_correct
    for idx in sorted_idx:
        total_count += 1
        if gt_list[idx] == correct_label:
            correct_count += 1
            precision = correct_count/float(total_count)
            precision_list.append( precision )
            recall = correct_count / float(total_correct)
            F1_list.append(  2*(precision*recall)/(recall+precision) )
            false_neg_num = total_correct - correct_count
        rest_num = len(sorted_idx) - total_count
        true_neg_num = rest_num - false_neg_num
        acc_list.append( (correct_count + true_neg_num) / float(len(sorted_idx)) )
    return np.mean(precision_list), np.max(F1_list), np.max(acc_list)

def safe_normalization(weight):
    weight_sum = torch.sum(weight, dim = 1, keepdim=True)
    return weight / (weight_sum + 0.000000000001)

def compute_cosine_sim(source, target):
    #assume that two matrices have been normalized
    C = target.permute(0,2,1)
    cos_sim_st = torch.bmm(source, C)
    cos_sim_ts = cos_sim_st.permute(0,2,1)
    return cos_sim_st, cos_sim_ts 

def weighted_average(cosine_sim, weight):
    #assume that weight are normalized
    return (cosine_sim * weight).mean(dim = 1)

def max_cosine_given_sim(cos_sim_st, target_w = None):
    cosine_sim_s_to_t, max_i = torch.max(cos_sim_st, dim = 1)
    #cosine_sim should have dimension (n_batch,n_set)
    sim_avg_st = cosine_sim_s_to_t.mean(dim = 1)
    if target_w is None:
        return sim_avg_st
    sim_w_avg_st = weighted_average(cosine_sim_s_to_t, target_w)
    return sim_avg_st, sim_w_avg_st

def lc_pred_dist(target, source, target_w, L1_losss_B, device):
    with torch.enable_grad():
        coeff_mat_s_to_t = nsd_loss.estimate_coeff_mat_batch_opt(target, source, L1_losss_B, device, coeff_opt ='rmsprop', lr = 0.05, max_iter = 1000)
    pred_embeddings = torch.bmm(coeff_mat_s_to_t, source)
    dist_st = torch.pow( torch.norm( pred_embeddings - target, dim = 2 ), 2)
    dist_avg_st = dist_st.mean(dim = 1)
    if target_w is None:
        return dist_avg_st
    dist_w_avg_st = weighted_average(dist_st, target_w)
    return dist_avg_st, dist_w_avg_st

def check_OOV(s_sent_emb, t_sent_emb):
    OOV_first = 0
    OOV_second = 0
    if np.sum(np.abs(s_sent_emb)) == 0:
        OOV_first = 1
    if np.sum(np.abs(t_sent_emb)) == 0:
        OOV_second = 1
    OOV_all_sent = [OOV_first, OOV_second]
    return OOV_all_sent
