import argparse
import os, sys
import time
import math
import shutil
import torch
import torch.nn as nn
import gc

import model.model as model_code
from utils import nsd_loss
from utils.utils import seed_all_randomness, create_exp_dir, save_checkpoint, load_emb_file_to_dict, load_emb_file_to_tensor, load_corpus, output_parallel_models, str2bool, compute_freq_prob_idx2word
from transformers import get_linear_schedule_with_warmup

parser = argparse.ArgumentParser(description='PyTorch Neural Set Decoder for Sentnece Embedding')

###path
parser.add_argument('--data', type=str, default='./data/processed/wackypedia/',
                    help='location of the data corpus')
parser.add_argument('--tensor_folder', type=str, default='tensors',
                    help='location of the data as tensors within the data folder')
parser.add_argument('--training_file', type=str, default='train.pt',
                    help='location of training file')
parser.add_argument('--save', type=str,  default='./models/Wacky',
                    help='path to save the final model')

# embeddings
# source embedding (pattern/relation word embedding)
parser.add_argument('--source_emsize', type=int, default=0,
                    help='size of word embeddings')
parser.add_argument('--update_source_emb', default=False, action='store_true',
                    help='Whether to update source embedding')
parser.add_argument('--source_emb_file', type=str, default='',
                    help='path to the file of a word embedding file')
parser.add_argument('--source_emb_source', type=str, default='ext',
                    help='Could be ext (external), rand or ewe (encode word embedding)')

#target embedding
parser.add_argument('--target_emsize', type=int, default=0,
                    help='size of entity pair embeddings')
parser.add_argument('--update_target_emb', default=False, action='store_true',
                    help='Whether to update target embedding')
parser.add_argument('--target_emb_source', type=str, default='ext',
                    help='Could be ext (external), rand or ewe (encode word embedding)')
parser.add_argument('--target_emb_file', type=str, default='',
                    help='Location of the target embedding file')

#both
parser.add_argument('--en_model', type=str, default='LSTM',
                    help='type of encoder model (LSTM, LSTM+TRANS, TRANS+LSTM, TRANS)')

parser.add_argument('--dropouti', type=float, default=0.4,
                    help='dropout for input embedding layers (0 = no dropout)')
parser.add_argument('--dropoute', type=float, default=0.1,
                    help='dropout to remove words from embedding layer (0 = no dropout)')
parser.add_argument('--dropout', type=float, default=0.4,
                    help='dropout applied to the output layer (0 = no dropout) in case of LSTM, transformer dropouts in case of TRANS')
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
parser.add_argument('--positional_option', type=str, default='linear',
                    help='options of encode positional embedding into models (linear, cat, add)')
parser.add_argument('--dropoutp', type=float, default=0.5,
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
parser.add_argument('--dropout_prob_trans', type=float, default=0.1,
                    help='hidden_dropout_prob and attention_probs_dropout_prob in Transformer')
#coeff
parser.add_argument('--w_loss_coeff', type=float, default=0.1,
                    help='weights for coefficient prediction loss')
parser.add_argument('--L1_losss_B', type=float, default=0.2,
                    help='L1 loss for the coefficient matrix')
parser.add_argument('--coeff_opt', type=str, default='lc',
                    help='Could be max, lc, maxlc')
parser.add_argument('--coeff_opt_algo', type=str, default='rmsprop',
                    help='Could be sgd_bmm, sgd, asgd, adagrad, rmsprop, and adam')

#training
parser.add_argument('--optimizer', type=str, default="SGD",
                    help='optimization algorithm. Could be SGD, Adam or AdamW')
parser.add_argument('--optimizer_target', type=str, default="SGD",
                    help='optimization algorithm for target embs. Could be SGD or Adam')
parser.add_argument('--optimizer_auto', type=str, default="SGD",
                    help='optimization algorithm for autoencoder. Could be SGD or Adam')
parser.add_argument('--lr', type=float, default=1,
                    help='initial learning rate')
parser.add_argument('--lr2_divide', type=float, default=1.0,
                    help='drop this ratio for the learning rate of the second LSTM')
parser.add_argument('--clip', type=float, default=0.25,
                    help='gradient clipping')
parser.add_argument('--epochs', type=int, default=20,
                    help='upper epoch limit')
parser.add_argument('--batch_size', type=int, default=200, metavar='N',
                    help='batch size')
parser.add_argument('--small_batch_size', type=int, default=-1,
                    help='the batch size for computation. batch_size should be divisible by small_batch_size.\
                     In our implementation, we compute gradients with small_batch_size multiple times, and accumulate the gradients\
                     until batch_size is reached. An update step is then performed.')
parser.add_argument('--loss', type=str, default='',
                    help='Can be "" or "bpr"')
parser.add_argument('--eps', type=float, default=1e-8,
                    help='epsilon for numeric precision')
parser.add_argument('--wdecay', type=float, default=1e-6,
                    help='weight decay applied to all weights of enc-dec optimizers')
parser.add_argument('--wdecay_target', type=float, default=0,
                    help='weight decay applied to target emb')
parser.add_argument('--nonmono', type=int, default=1,
                    help='decay learning rate after seeing how many validation performance drop')
parser.add_argument('--warmup_proportion', type=float, default=0,
                    help='fraction of warmup steps in case of AdamW with linear warmup')
parser.add_argument('--training_split_num', type=int, default=2,
                    help='We want to split training corpus into how many subsets. Splitting training dataset seems to make pytorch run much faster and we can store and eval the model more frequently')
parser.add_argument('--valid_per_epoch', type=int, default=2,
                    help='Number of times we want to run through validation data and save model within an epoch')
parser.add_argument('--copy_training', type=str2bool, nargs='?', default=True,
                    help='turn off this option to save some cpu memory when loading training data')
parser.add_argument('--rare', default=False, action='store_true',
                    help='emphasize on rare entity pairs')
parser.add_argument('--uniform_src', default=False, action='store_true',
                    help='uniform emphasis on words in sent patterns/relations')
parser.add_argument('--skip_val', default=False, action='store_true',
                    help='skip validation - use when train set is entire corpus')
parser.add_argument('--auto_w', type=float, default=0,
                    help='Weights for autoencoder loss')
parser.add_argument('--auto_avg', type=str2bool, nargs='?', default=False,
                    help='Average bases for autoencoder loss')
parser.add_argument('--pre_avg', type=str2bool, nargs='?', default=False,
                    help='Average sent pattern word embs for autoencoder loss')
parser.add_argument('--lr_auto', type=float, default=1,
                    help='Autoencoder learning rate')

###system
parser.add_argument('--seed', type=int, default=1111,
                    help='random seed')
parser.add_argument('--randomness', type=str2bool, nargs='?', default=True,
                    help='use randomness')
parser.add_argument('--cuda', type=str2bool, nargs='?', default=True,
                    help='use CUDA')
parser.add_argument('--single_gpu', default=False, action='store_true',
                    help='use single GPU')
parser.add_argument('--log-interval', type=int, default=200, metavar='N',
                    help='report interval')
parser.add_argument('--continue_train', action='store_true',
                    help='continue train from a checkpoint')



args = parser.parse_args()

########################
print("Set up environment")
########################
assert args.training_split_num >= args.valid_per_epoch

if args.coeff_opt == 'maxlc':
    current_coeff_opt = 'max'
else:
    current_coeff_opt = args.coeff_opt

if args.small_batch_size < 0:
    args.small_batch_size = args.batch_size


assert args.batch_size % args.small_batch_size == 0, 'batch_size must be divisible by small_batch_size'

# Equal basis assumption if no kb basis provided
if args.n_basis_kb < 0:
    args.n_basis_kb = args.n_basis


if not args.continue_train:
    args.save = '{}-{}'.format(args.save, time.strftime("%Y%m%d-%H%M%S"))
    create_exp_dir(args.save, scripts_to_save=['./src/main.py', './src/model/model.py', './src/utils/nsd_loss.py'])

def logging(s, print_=True, log_=True):
    if print_:
        print(s)
        sys.stdout.flush()
    if log_:
        with open(os.path.join(args.save, 'log.txt'), 'a+') as f_log:
            f_log.write(s + '\n')

# Set the random seed manually for reproducibility.
seed_all_randomness(args.seed,args.cuda,randomness=args.randomness)

logging('Args: {}'.format(args))

########################
print("Loading data")
########################

device = torch.device("cuda" if args.cuda else "cpu")

idx2word_freq, target_idx2word_freq, dataloader_train_arr, dataloader_val, dataloader_val_shuffled, max_sent_len = \
    load_corpus(args.data, args.batch_size, args.batch_size, device, args.tensor_folder, args.training_file, args.training_split_num, args.copy_training, skip_val= args.skip_val)


def counter_to_tensor(idx2word_freq, device, rare, smooth_alpha=0):
    total = len(idx2word_freq)
    w_freq = torch.zeros(total, dtype=torch.float, device = device, requires_grad = False)
    for i in range(total):
        # w_freq[i] = math.sqrt(idx2word_freq[x][1])
        if rare:
            if i == 0: print("Emphasizing on the RARE")
            if smooth_alpha == 0:
                if i == 0: print("No alpha-smoothing")
                w_freq[i] = idx2word_freq[i][1]
            else:
                if i == 0:
                    print("Using alpha-smoothing")
                    compute_freq_prob_idx2word(idx2word_freq)
                w_freq[i] = (smooth_alpha + idx2word_freq[i][-1]) / smooth_alpha
        else:
            if i == 0: print("Using UNIFORM emphasis")
            w_freq[i] = 1
    w_freq[0] = -1
    return w_freq

# Initialize or load source embeddings
source_emb = torch.tensor([0.])
extra_init_idx = []
if len(args.source_emb_file) > 0:
    source_emb, source_emb_size, extra_init_idx = load_emb_file_to_tensor(args.source_emb_file, device, idx2word_freq)
    source_emb = source_emb / (0.000000000001 + source_emb.norm(dim = 1, keepdim=True))
    source_emb.requires_grad = args.update_source_emb
    print("loading ", args.source_emb_file)
else:
    if args.source_emb_source == 'ewe':
        source_emb_size = args.source_emsize
        print("Using word embedding from encoder")
    elif args.source_emb_source == 'rand' and args.update_source_emb == True:
        source_emb_size = args.source_emsize
        source_emb = torch.randn(len(idx2word_freq), source_emb_size, device = device, requires_grad = False)
        source_emb = source_emb / (0.000000000001 + source_emb.norm(dim = 1, keepdim=True))
        source_emb.requires_grad = True
        print("Initialize source embedding randomly")
    else:
        print("We don't support such source_emb_source " + args.source_emb_source + ", update_source_emb ", args.update_source_emb, ", and source_emb_file "+ args.source_emb_file)
        sys.exit(1)

# Load target embeddings (for now target embeddings are assumed to be always loaded)
# TODO: Add random target embedding scenario?
if args.target_emb_source == 'ext' and len(args.target_emb_file) > 0:
    target_emb_dict, target_emb_sz = load_emb_file_to_dict(args.target_emb_file)
    num_entpairs = len(target_emb_dict)
    target_emb = torch.empty(num_entpairs, target_emb_sz, device=device, requires_grad=False)
    for entpair, emb in target_emb_dict.items():
        index = int(entpair[2:])
        val = torch.tensor(emb, device = device, requires_grad = False)
        target_emb[index,:] = val
    target_emb.requires_grad = args.update_target_emb
elif args.target_emb_source == 'rand' and args.update_target_emb == True and args.target_emsize > 0:
    target_emb_sz = args.target_emsize
    target_emb = torch.randn(len(target_idx2word_freq), target_emb_sz, device = device, requires_grad = False)
    target_emb = target_emb / (0.000000000001 + target_emb.norm(dim = 1, keepdim=True))
    target_emb.requires_grad = True
    print("Initialize target embedding randomly")
else:
    print("We don't support such target_emb_source " + args.target_emb_source + ", update_target_emb ", args.update_target_emb, ", and target_emb_file " + args.target_emb_file)
    sys.exit(1)

if args.trans_nhid < 0:
    if args.target_emsize > 0:
        args.trans_nhid = args.target_emsize
    else:
        args.trans_nhid = target_emb_sz

# Weight of each pattern/relation
print("Computing weight for entity pairs")
target_freq = counter_to_tensor(target_idx2word_freq, device, args.rare)

if args.auto_w > 0:
    print("Computing weight for words in sent pats/rels")
    feature_uniform = counter_to_tensor(idx2word_freq, device, not args.uniform_src, smooth_alpha=1e-4)
    feature_linear_layer = torch.randn(source_emb_size, target_emb_sz, device=device, requires_grad=True)
else:
    feature_linear_layer = torch.zeros(0, device=device)
########################
print("Building models")
########################

ntokens = len(idx2word_freq)
encoder = model_code.SEQ2EMB(args.en_model.split('+'), ntokens, args.source_emsize, args.nhid, args.nlayers,
                             args.dropout, args.dropouti, args.dropoute, max_sent_len, source_emb, extra_init_idx, args.encode_trans_layers, args.trans_nhid)

if args.nhidlast2 < 0:
    args.nhidlast2 = encoder.output_dim

decoder = model_code.EMB2SEQ(args.de_model.split('+'), args.de_coeff_model, encoder.output_dim, args.nhidlast2, source_emb_size, target_emb_sz, args.nlayers_dec, max(args.n_basis, args.n_basis_kb), positional_option = args.positional_option, dropoutp= args.dropoutp, trans_layers = args.trans_layers, using_memory =  args.de_en_connection, dropout_prob_trans = args.dropout_prob_trans, dropout_prob_lstm=args.dropout_prob_lstm)

if args.de_en_connection and decoder.trans_dim is not None and encoder.output_dim != decoder.trans_dim:
    print("dimension mismatch. The encoder output dimension is ", encoder.output_dim, " and the transformer dimension in decoder is ", decoder.trans_dim)
    sys.exit(1)

import torch.nn.init as weight_init
def initialize_weights(net, normal_std):
    for name, param in net.named_parameters():
        if 'bias' in name or 'rnn' not in name:
            continue
        print("normal init "+name+" with std"+str(normal_std) )
        weight_init.normal_(param, std = normal_std)

parallel_encoder, parallel_decoder = output_parallel_models(args.cuda, args.single_gpu, encoder, decoder)

total_params = sum(x.data.nelement() for x in encoder.parameters())
logging('Encoder total parameters: {}'.format(total_params))
total_params = sum(x.data.nelement() for x in decoder.parameters())
logging('Decoder total parameters: {}'.format(total_params))

########################
print("Training")
########################


def evaluate(dataloader, target_emb, current_coeff_opt):
    # Turn on evaluation mode which disables dropout.
    encoder.eval()
    decoder.eval()
    total_loss = 0
    total_loss_set = 0
    total_loss_set_reg = 0
    total_loss_set_div = 0
    total_loss_set_neg = 0
    total_loss_coeff_pred = 0.
    total_loss_set_auto = 0.
    total_loss_set_neg_auto = 0.

    with torch.no_grad():
        for i_batch, sample_batched in enumerate(dataloader):
            feature, target, kb_marker, num_basis = sample_batched

            output_emb_last, output_emb = parallel_encoder(feature)
            basis_pred, coeff_pred =  parallel_decoder(output_emb_last, output_emb, predict_coeff_sum = True)
            if len(args.target_emb_file) > 0 or args.target_emb_source == 'rand':
                input_emb = target_emb
            elif args.target_emb_source == 'ewe':
                input_emb = encoder.encoder.weight.detach()

            compute_target_grad = False

            # Changed input emb to target
            loss_set, loss_set_reg, loss_set_div, loss_set_neg, loss_coeff_pred = nsd_loss.compute_loss_set(output_emb_last, basis_pred, coeff_pred, input_emb, target, args.L1_losss_B, device, target_freq, current_coeff_opt, compute_target_grad, args.coeff_opt_algo, args.loss, kb_marker, num_basis, args.n_basis, args.n_basis_kb)
            if args.auto_w > 0:
                if args.auto_avg:
                    basis_pred_auto_compressed = basis_pred.mean(dim=1).unsqueeze(dim=1)
                else:
                    basis_pred_auto_compressed = basis_pred

                loss_set_auto, _, _, loss_set_neg_auto, _ = nsd_loss.compute_loss_set(output_emb_last, \
                                                                                      basis_pred_auto_compressed, \
                                                                                      coeff_pred, \
                                                                                      source_emb, \
                                                                                      feature, \
                                                                                      args.L1_losss_B, \
                                                                                      device, \
                                                                                      feature_uniform, \
                                                                                      current_coeff_opt, \
                                                                                      # compute_target_grad should be
                                                                                      # false as input embs are fixed
                                                                                      True, \
                                                                                      args.coeff_opt_algo, \
                                                                                      args.loss, \
                                                                                      kb_marker, \
                                                                                      num_basis, \
                                                                                      args.n_basis, \
                                                                                      args.n_basis_kb, \
                                                                                      target_linear_layer=feature_linear_layer, \
                                                                                      pre_avg=args.pre_avg)
                if torch.isnan(loss_set_auto):
                    sys.stdout.write('auto nan, ')
                    continue
            else:
                loss_set_auto = torch.tensor(0, device=device)
                loss_set_neg_auto = torch.tensor(0, device=device)
            # TODO: Add coeff loss here for bprloss if required
            # TODO: Implement autoencoder loss for bprloss
            if args.loss == 'bpr':
                loss = loss_set - loss_set_neg
                loss = - torch.mean(torch.log(args.eps + nn.Sigmoid()(-loss)))
                loss_set = torch.mean(loss_set)
                loss_set_neg = - torch.mean(loss_set_neg)
            else:
                loss = loss_set + loss_set_neg + args.w_loss_coeff*loss_coeff_pred + args.auto_w * (loss_set_auto + loss_set_neg_auto)

            batch_size = feature.size(0)
            total_loss += loss * batch_size
            total_loss_set += loss_set * batch_size
            total_loss_set_reg += loss_set_reg * batch_size
            total_loss_set_div += loss_set_div * batch_size
            total_loss_set_neg += loss_set_neg * batch_size
            total_loss_coeff_pred += loss_coeff_pred * batch_size
            total_loss_set_auto += loss_set_auto * batch_size
            total_loss_set_neg_auto += loss_set_neg_auto * batch_size


    return total_loss.item() / len(dataloader.dataset), total_loss_set.item() / len(dataloader.dataset), \
           total_loss_set_neg.item() / len(dataloader.dataset), total_loss_coeff_pred.item() / len(dataloader.dataset), \
           total_loss_set_reg.item() / len(dataloader.dataset), total_loss_set_div.item() / len(dataloader.dataset), \
           total_loss_set_auto.item() / len(dataloader.dataset), total_loss_set_neg_auto.item() / len(dataloader.dataset)


def train_one_epoch(dataloader_train, target_emb, lr, current_coeff_opt, split_i):
    start_time = time.time()
    total_loss = 0.
    total_loss_set = 0.
    total_loss_set_reg = 0.
    total_loss_set_div = 0.
    total_loss_set_neg = 0.
    total_loss_coeff_pred = 0.
    total_loss_set_auto = 0.
    total_loss_set_neg_auto = 0.

    encoder.train()
    decoder.train()
    for i_batch, sample_batched in enumerate(dataloader_train):
        feature, target, kb_marker, num_basis = sample_batched
        if args.update_target_emb: target_emb_optimizer.zero_grad()
        optimizer_e.zero_grad()
        optimizer_d.zero_grad()
        if args.auto_w > 0: optimizer_auto.zero_grad()
        output_emb_last, output_emb = parallel_encoder(feature)
        basis_pred, coeff_pred =  parallel_decoder(output_emb_last, output_emb, predict_coeff_sum = True)
        if len(args.target_emb_file) > 0  or args.target_emb_source == 'rand':
            input_emb = target_emb
        elif args.target_emb_source == 'ewe':
            input_emb = encoder.encoder.weight.detach()
        compute_target_grad = args.update_target_emb
        loss_set, loss_set_reg, loss_set_div, loss_set_neg, loss_coeff_pred = nsd_loss.compute_loss_set(output_emb_last, \
                                                                                                        basis_pred, \
                                                                                                        coeff_pred, \
                                                                                                        input_emb, \
                                                                                                        target, \
                                                                                                        args.L1_losss_B, \
                                                                                                        device, \
                                                                                                        target_freq, \
                                                                                                        current_coeff_opt, \
                                                                                                        compute_target_grad, \
                                                                                                        args.coeff_opt_algo, \
                                                                                                        args.loss, \
                                                                                                        kb_marker, \
                                                                                                        num_basis, \
                                                                                                        args.n_basis, \
                                                                                                        args.n_basis_kb)
        if torch.isnan(loss_set).any():
            sys.stdout.write('nan, ')
            continue

        if args.auto_w > 0:
            if args.auto_avg:
                basis_pred_auto_compressed = basis_pred.mean(dim=1).unsqueeze(dim=1)
            else:
                basis_pred_auto_compressed = basis_pred

            loss_set_auto, _, _, loss_set_neg_auto, _ = nsd_loss.compute_loss_set(output_emb_last, \
                                                                                  basis_pred_auto_compressed, \
                                                                                  coeff_pred, \
                                                                                  source_emb, \
                                                                                  feature, \
                                                                                  args.L1_losss_B, \
                                                                                  device, \
                                                                                  feature_uniform, \
                                                                                  current_coeff_opt, \
                                                                                  True, \
                                                                                  args.coeff_opt_algo, \
                                                                                  args.loss, \
                                                                                  kb_marker, \
                                                                                  num_basis, \
                                                                                  args.n_basis, \
                                                                                  args.n_basis_kb, \
                                                                                  target_linear_layer=feature_linear_layer, \
                                                                                  pre_avg=args.pre_avg)
            if torch.isnan(loss_set_auto):
                sys.stdout.write('auto nan, ')
                continue
        else:
            loss_set_auto = torch.tensor(0, device=device)
            loss_set_neg_auto = torch.tensor(0, device=device)
        # TODO: Add coeff loss here for bprloss if required
        # TODO: Implement autoencoder loss for bpr case
        if args.loss == 'bpr':
            loss = loss_set - loss_set_neg
            loss = - torch.mean(torch.log(args.eps + nn.Sigmoid()(-loss)))
            loss_set = torch.mean(loss_set)
            loss_set_neg = - torch.mean(loss_set_neg)
        else:
            loss = loss_set + args.w_loss_coeff * loss_coeff_pred
            if -loss_set_neg > 1:
                loss -= loss_set_neg
            else:
                loss += loss_set_neg
            # Autoencoder loss
            loss += args.auto_w * loss_set_auto
            if -loss_set_neg_auto > 1:
                loss -= args.auto_w * loss_set_neg_auto
            else:
                loss += args.auto_w * loss_set_neg_auto

        loss *= args.small_batch_size / args.batch_size
        total_loss += loss.item()

        total_loss_set += loss_set.item() * args.small_batch_size / args.batch_size
        total_loss_set_reg += loss_set_reg.item() * args.small_batch_size / args.batch_size
        total_loss_set_div += loss_set_div.item() * args.small_batch_size / args.batch_size
        total_loss_set_neg += loss_set_neg.item() * args.small_batch_size / args.batch_size
        total_loss_coeff_pred += loss_coeff_pred.item() * args.small_batch_size / args.batch_size
        total_loss_set_auto += loss_set_auto * args.small_batch_size / args.batch_size
        total_loss_set_neg_auto += loss_set_neg_auto * args.small_batch_size / args.batch_size

        loss.backward()

        gc.collect()

        torch.nn.utils.clip_grad_norm_(encoder.parameters(), args.clip)
        torch.nn.utils.clip_grad_norm_(decoder.parameters(), args.clip)
        optimizer_e.step()
        if len(args.target_emb_file) == 0 and args.target_emb_source == 'ewe':
            encoder.encoder.weight.data[0,:] = 0

        optimizer_d.step()
        # Changed to using pytorch optimizer
        if args.update_target_emb:
            target_emb_optimizer.step()
            # Update autoencoder optimizer
            if args.auto_w > 0: optimizer_auto.step()
            if args.target_emb_source != 'ewe': target_emb.data[0,:] = 0
            target_emb.data = target_emb.data / (0.000000000001 + target_emb.data.norm(dim = 1, keepdim=True))


        if args.optimizer == 'AdamW':
            scheduler_e.step()
            scheduler_d.step()

        if i_batch % args.log_interval == 0 and i_batch > 0:
            cur_loss = total_loss / args.log_interval
            cur_loss_set = total_loss_set / args.log_interval
            cur_loss_set_reg = total_loss_set_reg / args.log_interval
            cur_loss_set_div = total_loss_set_div / args.log_interval
            cur_loss_set_neg = total_loss_set_neg / args.log_interval
            cur_loss_coeff_pred = total_loss_coeff_pred / args.log_interval
            cur_loss_set_auto = total_loss_set_auto / args.log_interval
            cur_loss_set_neg_auto = total_loss_set_neg_auto / args.log_interval
            elapsed = time.time() - start_time
            if args.auto_w > 0:
                logging('| e {:3d} {:3d} | {:5d}/{:5d} b | lr-enc {:.6f} | lr-dec {:.6f} | lr-auto {:.6f} | ms/batch {:5.2f} | '
                        'l {:5.2f} | l_f {:5.4f} + {:5.4f} = {:5.4f} | l_f_auto {:5.4f} + {:5.4f} = {:5.4f} | l_coeff {:5.3f} | reg {:5.2f} | div {:5.2f} '.format(
                    epoch, split_i, i_batch, len(dataloader_train.dataset) // args.batch_size, optimizer_e.param_groups[0]['lr'],optimizer_d.param_groups[0]['lr'], optimizer_auto.param_groups[0]['lr'], elapsed * 1000 / args.log_interval, cur_loss, cur_loss_set, cur_loss_set_neg, cur_loss_set + cur_loss_set_neg, cur_loss_set_auto, cur_loss_set_neg_auto, cur_loss_set_auto + cur_loss_set_neg_auto, cur_loss_coeff_pred, cur_loss_set_reg, cur_loss_set_div))
            else:
                logging(
                    '| e {:3d} {:3d} | {:5d}/{:5d} b | lr-enc {:.6f} | lr-dec {:.6f} | ms/batch {:5.2f} | l {:5.2f} | l_f {:5.4f} + {:5.4f} = {:5.4f} | l_coeff {:5.3f} | reg {:5.2f} | div {:5.2f} '.format(
                        epoch, split_i, i_batch, len(dataloader_train.dataset) // args.batch_size,
                        optimizer_e.param_groups[0]['lr'], optimizer_d.param_groups[0]['lr'],
                        elapsed * 1000 / args.log_interval, cur_loss,
                        cur_loss_set, cur_loss_set_neg, cur_loss_set + cur_loss_set_neg, cur_loss_coeff_pred,
                        cur_loss_set_reg, cur_loss_set_div))
            #if args.coeff_opt == 'maxlc' and current_coeff_opt == 'max' and cur_loss_set + cur_loss_set_neg < -0.02:
            if args.coeff_opt == 'maxlc' and current_coeff_opt == 'max' and cur_loss_set + cur_loss_set_neg < -0.02:
                current_coeff_opt = 'lc'
                print("switch to lc")
            total_loss = 0.
            total_loss_set = 0.
            total_loss_set_reg = 0.
            total_loss_set_div = 0.
            total_loss_set_neg = 0.
            total_loss_coeff_pred = 0.
            total_loss_set_auto = 0.
            total_loss_set_neg_auto = 0.
            start_time = time.time()

    return current_coeff_opt


if args.optimizer == 'SGD':
    optimizer_e = torch.optim.SGD(encoder.parameters(), lr=args.lr, weight_decay=args.wdecay)
    optimizer_d = torch.optim.SGD(decoder.parameters(), lr=args.lr, weight_decay=args.wdecay)
    if args.update_target_emb: target_emb_lr = args.lr/args.lr2_divide/10.0
elif args.optimizer == 'Adam':
    optimizer_e = torch.optim.Adam(encoder.parameters(), lr=args.lr, weight_decay=args.wdecay)
    optimizer_d = torch.optim.Adam(decoder.parameters(), lr=args.lr, weight_decay=args.wdecay)
    if args.update_target_emb: target_emb_lr = 1.0/args.lr2_divide
else:
    optimizer_e = torch.optim.AdamW(encoder.parameters(), lr=args.lr, weight_decay=args.wdecay)
    optimizer_d = torch.optim.AdamW(decoder.parameters(), lr=args.lr, weight_decay=args.wdecay)
    num_training_steps = sum([len(train_split) for train_split in dataloader_train_arr]) * args.epochs
    num_warmup_steps = args.warmup_proportion * num_training_steps
    if args.update_target_emb: target_emb_lr = 1.0/args.lr2_divide
    print("Warmup steps:{}, Total steps:{}".format(num_warmup_steps, num_training_steps))
    scheduler_e = get_linear_schedule_with_warmup(optimizer_e, num_warmup_steps=num_warmup_steps, num_training_steps=num_training_steps)
    scheduler_d = get_linear_schedule_with_warmup(optimizer_d, num_warmup_steps=num_warmup_steps, num_training_steps=num_training_steps)

if args.update_target_emb:
    if args.optimizer_target == 'SGD':
        target_emb_optimizer = torch.optim.SGD([target_emb], lr=target_emb_lr, weight_decay=args.wdecay_target)
    elif args.optimizer_target == 'Adam':
        target_emb_optimizer = torch.optim.Adam([target_emb], lr=target_emb_lr, weight_decay=args.wdecay_target)
if args.auto_w > 0:
    if args.optimizer_auto == 'SGD':
        optimizer_auto = torch.optim.SGD([feature_linear_layer], lr=args.lr_auto)
    elif args.optimizer_auto == 'Adam':
        optimizer_auto = torch.optim.Adam([feature_linear_layer], lr=args.lr_auto)

lr = args.lr
best_val_loss = None
nonmono_count = 0
saving_freq = int(math.floor(args.training_split_num / args.valid_per_epoch))

steps = 0
checkpoint_epochs = {15, 20, 25, 30, 50}
for epoch in range(1, args.epochs+1):
    epoch_start_time = time.time()
    for i in range(len(dataloader_train_arr)):
        current_coeff_opt = train_one_epoch(dataloader_train_arr[i], target_emb, lr, current_coeff_opt, i)
        steps += len(dataloader_train_arr[i])
        if i != args.training_split_num - 1 and (i + 1) % saving_freq != 0:
            continue

        # dataloader_val_org
        if dataloader_val is not None:
            val_loss_all, val_loss_set, val_loss_set_neg, val_loss_ceoff_pred, val_loss_set_reg, val_loss_set_div, val_loss_set_auto, val_loss_set_neg_auto = evaluate(dataloader_val, target_emb, current_coeff_opt)
            logging('-' * 89)
            logging('| end of epoch {:3d} split {:3d} | time: {:5.2f}s | lr {:.6f} | valid loss {:5.2f} | l_f {:5.4f} + {:5.4f} = {:5.4f} | l_f_auto {:5.4f} + {:5.4f} = {:5.4f}| l_coeff {:5.2f} | reg {:5.2f} | div {:5.2f} | '
                    .format(epoch, i, (time.time() - epoch_start_time), lr,
                                               val_loss_all, val_loss_set, val_loss_set_neg, val_loss_set + val_loss_set_neg, val_loss_set_auto, val_loss_set_neg_auto,  val_loss_set_auto + val_loss_set_neg_auto, val_loss_ceoff_pred, val_loss_set_reg, val_loss_set_div))
            logging('-' * 89)

        # dataloader_val_shuffled
        if dataloader_val_shuffled is not None:
            val_loss_all, val_loss_set, val_loss_set_neg, val_loss_ceoff_pred, val_loss_set_reg, val_loss_set_div, val_loss_set_auto, val_loss_set_neg_auto = evaluate(dataloader_val_shuffled, target_emb, current_coeff_opt)
            logging('-' * 89)
            logging('| Shuffled | time: {:5.2f}s | lr {:.6f} | valid loss {:5.2f} | l_f {:5.4f} + {:5.4f} = {:5.4f} | l_f_auto {:5.4f} + {:5.4f} = {:5.4f} | l_coeff {:5.2f} | reg {:5.2f} | div {:5.2f} | '
                    .format((time.time() - epoch_start_time), lr,
                                               val_loss_all, val_loss_set, val_loss_set_neg, val_loss_set + val_loss_set_neg, val_loss_set_auto, val_loss_set_neg_auto,  val_loss_set_auto + val_loss_set_neg_auto, val_loss_ceoff_pred, val_loss_set_reg, val_loss_set_div))
            logging('-' * 89)

            val_loss_important = val_loss_set + val_loss_set_neg + val_loss_set_auto + val_loss_set_neg_auto

            if not best_val_loss or val_loss_important < best_val_loss:
                save_checkpoint(encoder, decoder, optimizer_e, optimizer_d, source_emb, target_emb, args.save)
                logging('Models Saved')
                best_val_loss = val_loss_important
            else:
                nonmono_count += 1

        if epoch in checkpoint_epochs:
            epoch_save_loc = os.path.join(args.save, "ep{}".format(epoch))
            create_exp_dir(epoch_save_loc)
            model_files = [f for f in os.listdir(args.save) if f.endswith(".pt")]
            if len(model_files) > 0:
                [shutil.copy(os.path.join(args.save, f), epoch_save_loc) for f in model_files]
                logging("Best model till epoch {} copied to {}".format(epoch, epoch_save_loc))
            else:
                save_checkpoint(encoder, decoder, optimizer_e, optimizer_d, source_emb, target_emb, epoch_save_loc)
                logging('Model saved for epoch {}'.format(epoch))

        print('='*80)

        # Do not anneal lr when in warmup phase
        if args.optimizer == 'AdamW' and steps < num_warmup_steps:
            continue

        if nonmono_count >= args.nonmono:
            # Anneal the learning rate if no improvement has been seen in the validation dataset.
            nonmono_count = 0
            lr /= 4.0
            for param_group in optimizer_e.param_groups:
                param_group['lr'] = lr
            for param_group in optimizer_d.param_groups:
                param_group['lr'] = lr
            if args.update_target_emb:
                for param_group in target_emb_optimizer.param_groups:
                    param_group['lr'] = lr / args.lr * target_emb_lr
            if args.auto_w > 0:
                for param_group in optimizer_auto.param_groups:
                    param_group['lr'] = lr / args.lr * args.lr_auto
