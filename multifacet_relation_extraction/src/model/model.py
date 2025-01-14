import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

from model.embed_regularize import embedded_dropout
from model.locked_dropout import LockedDropout
import model.model_trans as model_trans
import sys

class MatrixReconstruction(nn.Module):
    def __init__(self, batch_size, ntopic, nbow, device):
        super(MatrixReconstruction, self).__init__()
        self.coeff = nn.Parameter(torch.randn(batch_size, ntopic, nbow, device=device, requires_grad=True))
        self.device = device
    
    def compute_coeff_pos(self):
        self.coeff.data = self.coeff.clamp(0.0, 1.0)
    
    def forward(self, input):
        result = self.coeff.matmul(input)
        return result

class RNN_decoder(nn.Module):
    def __init__(self, model_type, emb_dim, ninp, nhid, nlayers, dropout_prob):
        super(RNN_decoder, self).__init__()
        if model_type in ['LSTM', 'GRU']:
            print("RNN decoder dropout:", dropout_prob)
            self.rnn = getattr(nn, model_type)(emb_dim, nhid, nlayers, dropout=dropout_prob)
        else:
            try:
                nonlinearity = {'RNN_TANH': 'tanh', 'RNN_RELU': 'relu'}[model_type]
            except KeyError:
                raise ValueError( """An invalid option for `--model` was supplied,
                                 options are ['LSTM', 'GRU', 'RNN_TANH' or 'RNN_RELU']""")
            self.rnn = nn.RNN(emb_dim, nhid, nlayers, nonlinearity=nonlinearity, dropout=dropout_prob)
        
        if model_type == 'LSTM':
            self.init_hid_linear_1 = nn.ModuleList([nn.Linear(ninp, nhid) for i in range(nlayers)])
            self.init_hid_linear_2 = nn.ModuleList([nn.Linear(ninp, nhid) for i in range(nlayers)])
            for i in range(nlayers):
                self.init_hid_linear_1[i].weight.data.uniform_(-.1,.1)
                self.init_hid_linear_1[i].bias.data.uniform_(-.5,.5)
                self.init_hid_linear_2[i].weight.data.uniform_(-.1,.1)
                self.init_hid_linear_2[i].bias.data.uniform_(-.5,.5)
        self.nlayers = nlayers
        self.model_type = model_type

    def forward(self, input_init, emb):
        hidden_1 = torch.cat( [self.init_hid_linear_1[i](input_init).unsqueeze(dim = 0) for i in range(self.nlayers)], dim = 0 )
        hidden_2 = torch.cat( [self.init_hid_linear_2[i](input_init).unsqueeze(dim = 0) for i in range(self.nlayers)], dim = 0 )
        hidden = (hidden_1, hidden_2)
        
        output, hidden = self.rnn(emb, hidden)
        return output

class ext_emb_to_seq(nn.Module):
    def __init__(self, model_type_list, emb_dim, ninp, nhid, nlayers, n_basis, trans_layers, using_memory, add_position_emb, dropout_prob_trans, dropout_prob_lstm):
        super(ext_emb_to_seq, self).__init__()
        self.decoder_array = nn.ModuleList()
        input_dim = emb_dim
        self.trans_dim = None
        for model_type in model_type_list:
            if model_type == 'LSTM':
                model = RNN_decoder(model_type, input_dim, ninp, nhid, nlayers, dropout_prob_lstm)
                input_dim = nhid
            elif model_type == 'TRANS':
                model = model_trans.Transformer(model_type = model_type, hidden_size = input_dim, max_position_embeddings = n_basis, num_hidden_layers=trans_layers, add_position_emb = add_position_emb, decoder = using_memory, dropout_prob = dropout_prob_trans)
                self.trans_dim = input_dim
            else:
                print("model type must be either LSTM or TRANS")
                sys.exit(1)
            self.decoder_array.append( model )
        self.output_dim = input_dim

    def forward(self, input_init, emb, memory=None):
        hidden_states = emb
        for model in self.decoder_array:
            model_type = model.model_type
            if model_type == 'LSTM':
                hidden_states = model(input_init, hidden_states)
            elif model_type == 'TRANS':
                #If we want to use transformer by default at the end, we will want to reconsider reducing the number of permutes
                hidden_states = hidden_states.permute(1,0,2)
                hidden_states = model(hidden_states, memory)
                hidden_states = hidden_states[0].permute(1,0,2)
        return hidden_states

class EMB2SEQ(nn.Module):
    def __init__(self, model_type_list, coeff_model, ninp, nhid, outd, target_emb_sz, nlayers, n_basis, positional_option, dropoutp= 0.5, trans_layers=2, using_memory = False, dropout_prob_trans = 0.1,dropout_prob_lstm=0):
        super(EMB2SEQ, self).__init__()
        self.drop = nn.Dropout(dropoutp)
        self.n_basis = n_basis
        input_size = ninp
        add_position_emb = False
        if positional_option == 'linear':
            linear_mapping_dim = ninp
            self.init_linear_arr = nn.ModuleList([nn.Linear(ninp, linear_mapping_dim) for i in range(n_basis)])
            for i in range(n_basis):
                #It seems that the LSTM only learns well when bias is larger than weights at the beginning
                #If setting std in weight to be too large (e.g., 1), the loss might explode
                self.init_linear_arr[i].bias.data.uniform_(-.5,.5)
                self.init_linear_arr[i].weight.data.uniform_(-.1,.1)
            input_size = linear_mapping_dim
        elif positional_option == 'cat':
            position_emb_size = 100
            self.poistion_emb = nn.Embedding( n_basis, position_emb_size )
            self.linear_keep_same_dim = nn.Linear(position_emb_size + ninp, ninp)
            input_size = ninp
        elif positional_option == 'add':
            input_size = ninp
            add_position_emb = True
            if model_type_list[0] == 'LSTM':
                self.poistion_emb = nn.Embedding( n_basis, ninp )
            else:
                self.scale_factor = math.sqrt(ninp)

        self.positional_option = positional_option
        self.dep_learner = ext_emb_to_seq(model_type_list, input_size, ninp, nhid, nlayers, n_basis, trans_layers, using_memory, add_position_emb, dropout_prob_trans, dropout_prob_lstm)
        
        self.trans_dim = self.dep_learner.trans_dim
        self.out_linear = nn.Linear(self.dep_learner.output_dim, outd)
        self.final = nn.Linear(outd, target_emb_sz)
        
        self.coeff_model = coeff_model
        if coeff_model == "LSTM":
            coeff_nlayers = 1
            self.coeff_rnn = nn.LSTM(input_size+target_emb_sz , nhid, num_layers = coeff_nlayers , bidirectional = True)
            output_dim = nhid*2
        elif coeff_model == "TRANS":
            coeff_nlayers = 2
            self.coeff_trans = model_trans.Transformer(model_type ='TRANS', hidden_size =input_size + target_emb_sz, max_position_embeddings = n_basis, num_hidden_layers=coeff_nlayers, add_position_emb = False, decoder = False)
            output_dim = input_size+target_emb_sz
        half_output_dim = int(output_dim / 2)
        self.coeff_out_linear_1 = nn.Linear(output_dim, half_output_dim)
        self.coeff_out_linear_2 = nn.Linear(half_output_dim, half_output_dim)
        self.coeff_out_linear_3 = nn.Linear(half_output_dim, 2)
        self.init_weights()

    def init_weights(self):
        #necessary?
        initrange = 0.1
        self.out_linear.bias.data.zero_()
        self.out_linear.weight.data.uniform_(-initrange, initrange)
        self.final.weight.data.uniform_(-initrange, initrange)

    def forward(self, input_init, memory = None, predict_coeff_sum = False):
        def prepare_posi_emb(input, poistion_emb, drop):
            batch_size = input.size(1)
            n_basis = input.size(0)
            input_pos = torch.arange(n_basis,dtype=torch.long,device = input.get_device()).expand(batch_size,n_basis).permute(1,0)
            poistion_emb_input = poistion_emb(input_pos)
            poistion_emb_input = drop(poistion_emb_input)
            return poistion_emb_input

        input = input_init.expand(self.n_basis, input_init.size(0), input_init.size(1) )

        if self.positional_option == 'linear':
            emb_raw = torch.cat( [self.init_linear_arr[i](input_init).unsqueeze(dim = 0)  for i in range(self.n_basis) ] , dim = 0 )
            emb = self.drop(emb_raw)
        elif self.positional_option == 'cat':
            poistion_emb_input = prepare_posi_emb(input, self.poistion_emb, self.drop)
            emb = torch.cat( ( poistion_emb_input,input), dim = 2  )
            emb = self.linear_keep_same_dim(emb)
        elif self.positional_option == 'add':
            if self.dep_learner.decoder_array[0].model_type == "LSTM":
                poistion_emb_input = prepare_posi_emb(input, self.poistion_emb, self.drop)
                emb = input + poistion_emb_input
            else:
                emb = input * self.scale_factor

        output = self.dep_learner(input_init, emb, memory)
        output = self.out_linear(output)
        output = self.final(output)

        output_batch_first = output.permute(1,0,2)

        if not predict_coeff_sum:
            #output has dimension (n_batch, n_seq_len, n_emb_size)
            return output_batch_first
        else:
            coeff_input= torch.cat( (emb, output), dim = 2)
            if self.coeff_model == "LSTM":
                coeff_output, coeff_hidden = self.coeff_rnn(coeff_input.detach()) #default hidden state is 0
            elif self.coeff_model == "TRANS":
                hidden_states = coeff_input.detach().permute(1,0,2)
                hidden_states = self.coeff_trans(hidden_states)
                coeff_output = hidden_states[0].permute(1,0,2)

            coeff_pred_1 = F.relu(self.coeff_out_linear_1(coeff_output))
            coeff_pred_2 = F.relu(self.coeff_out_linear_2(coeff_pred_1))
            coeff_pred = self.coeff_out_linear_3(coeff_pred_2)
            coeff_pred_batch_first = coeff_pred.permute(1,0,2)
            return output_batch_first, coeff_pred_batch_first


class RNN_encoder(nn.Module):
    def __init__(self, model_type, ninp, nhid, nlayers, dropout):
        super(RNN_encoder, self).__init__()
        if model_type in ['LSTM', 'GRU']:
            self.rnn = getattr(nn, model_type)(ninp, nhid, nlayers, dropout=0, bidirectional = True)
        else:
            try:
                nonlinearity = {'RNN_TANH': 'tanh', 'RNN_RELU': 'relu'}[model_type]
            except KeyError:
                raise ValueError( """An invalid option for `--model` was supplied,
                                 options are ['LSTM', 'GRU', 'RNN_TANH' or 'RNN_RELU']""")
            self.rnn = nn.RNN(ninp, nhid, nlayers, nonlinearity=nonlinearity, dropout=0)
        
        self.use_dropout = True
        self.dropout = dropout
        self.lockdrop = LockedDropout()
        self.nlayers = nlayers
        self.model_type = model_type
    
    def forward(self, emb):
        output_org, hidden = self.rnn(emb)
        output = self.lockdrop(output_org, self.dropout if self.use_dropout else 0)
        return output

class RNN_pooler(nn.Module):
    def __init__(self, nhid):
        super(RNN_pooler, self).__init__()
        self.nhid = nhid
    # CHANGE BELOW TO ADD/REMOVE MAXPOOLING
    def forward(self, output, bsz):
        output_unpacked = output.view(output.size(0), bsz, 2, self.nhid)
        # NO MAXPOOLING
        # output_last = torch.cat( (output_unpacked[-1,:,0,:], output_unpacked[0,:,1,:]) , dim = 1)
        # MAXPOOLING
        output_last = torch.cat((torch.max(output_unpacked[:, :, 0, :], dim=0)[0], torch.max(output_unpacked[:, :, 1, :], dim=0)[0]), dim=1)
        return output_last

class TRANS_pooler(nn.Module):
    def __init__(self, method = 'last'):
        super(TRANS_pooler, self).__init__()
        self.method = method

    def forward(self, output):
        if self.method == 'last':
            output_last = output[-1,:,:]
        elif self.method == 'avg':
            output_last = torch.mean(output, dim = 0)
        return output_last


class seq_to_emb(nn.Module):
    def __init__(self, model_type_list, ninp, nhid, nlayers, dropout, max_sent_len, trans_layers, trans_nhid):
        super(seq_to_emb, self).__init__()
        self.encoder_array = nn.ModuleList()
        input_dim = ninp
        for i, model_type in enumerate(model_type_list):
            if model_type == 'LSTM':
                model = RNN_encoder(model_type, input_dim, nhid, nlayers, dropout)
                input_dim = nhid * 2
            elif model_type == 'TRANS':
                self.linear_trans_dim = None
                if input_dim != trans_nhid:
                    self.linear_trans_dim = nn.Linear(input_dim, trans_nhid)
                    
                if i == 0:
                    add_position_emb = True
                else:
                    add_position_emb = False
                model = model_trans.Transformer(model_type = model_type, hidden_size = trans_nhid, max_position_embeddings = max_sent_len, num_hidden_layers=trans_layers, add_position_emb = add_position_emb, dropout_prob=dropout)
                input_dim = trans_nhid
            else:
                print("model type must be either LSTM or TRANS")
                sys.exit(1)
            self.encoder_array.append( model )
        if model_type_list[-1] == 'LSTM':
            self.pooler = RNN_pooler(nhid)
        else:
            self.pooler = TRANS_pooler(method = 'last')
        
        self.model_type_list = model_type_list
        self.output_dim = input_dim

    def forward(self, emb):
        bsz = emb.size(1)
        hidden_states = emb
        for model in self.encoder_array:
            model_type = model.model_type
            if model_type == 'LSTM':
                hidden_states = model(hidden_states)
            elif model_type == 'TRANS':
                #If we want to use transformer by default at the end, we will want to reconsider reducing the number of permutes
                if self.linear_trans_dim is not None:
                    hidden_states = self.linear_trans_dim(hidden_states)
                hidden_states = hidden_states.permute(1,0,2)
                hidden_states = model(hidden_states)
                hidden_states = hidden_states[0].permute(1,0,2)
        if self.model_type_list[-1] == 'LSTM':
            output_emb = self.pooler(hidden_states, bsz)
        else:
            output_emb = self.pooler(hidden_states)
        return output_emb, hidden_states

class SEQ2EMB(nn.Module):
    """Container module with an encoder, a recurrent module, and a decoder."""

    def __init__(self, model_type_list, ntoken, ninp, nhid, nlayers, dropout, dropouti, dropoute, max_sent_len, external_emb, init_idx = [], trans_layers=2, trans_nhid=300):
        super(SEQ2EMB, self).__init__()
        self.lockdrop = LockedDropout()
        if len(external_emb) > 1 and ninp == 0:
            ntoken, ninp = external_emb.size()
            scale_factor = math.sqrt(ninp)
            self.encoder = nn.Embedding.from_pretrained(external_emb.clone() * scale_factor, freeze = False)
            if len(init_idx) > 0:
                print("Randomly initializes embedding for ", len(init_idx), " words")
                device = self.encoder.weight.data.get_device()
                extra_init_emb = torch.randn(len(init_idx), ninp, requires_grad = False, device = device)
                self.encoder.weight.data[init_idx, :] = extra_init_emb
        else:
            self.encoder = nn.Embedding(ntoken, ninp)
        self.use_dropout = True

        self.seq_summarizer =  seq_to_emb(model_type_list, ninp, nhid, nlayers, dropout, max_sent_len, trans_layers, trans_nhid)
        self.output_dim = self.seq_summarizer.output_dim

        self.dropoute = dropoute
        self.dropouti = dropouti

    def forward(self, input):
        emb = embedded_dropout(self.encoder, input.t(), dropout=self.dropoute if self.use_dropout else 0)
        emb = self.lockdrop(emb, self.dropouti if self.use_dropout else 0)

        output_last, output = self.seq_summarizer(emb)
        return output_last, output.permute(1,0,2)


class RNNModel(nn.Module):
    """Container module with an encoder, a recurrent module, and a decoder."""

    def __init__(self, rnn_type, ntoken, ninp, nhid, nhidlast, nlayers, 
                 dropout=0.5, dropouth=0.5, dropouti=0.5, dropoute=0.1, wdrop=0, 
                 tie_weights=False, ldropout=0.5, n_experts=10):
        super(RNNModel, self).__init__()
        self.use_dropout = True
        self.lockdrop = LockedDropout()
        self.encoder = nn.Embedding(ntoken, ninp)
        
        self.rnns = [torch.nn.LSTM(ninp if l == 0 else nhid, nhid if l != nlayers - 1 else nhidlast, 1, dropout=0) for l in range(nlayers)]
        if wdrop:
            self.rnns = [WeightDrop(rnn, ['weight_hh_l0'], dropout=wdrop if self.use_dropout else 0) for rnn in self.rnns]
        self.rnns = torch.nn.ModuleList(self.rnns)

        self.prior = nn.Linear(nhidlast, n_experts, bias=False)
        self.latent = nn.Sequential(nn.Linear(nhidlast, n_experts*ninp), nn.Tanh())
        self.decoder = nn.Linear(ninp, ntoken)

        # Optionally tie weights as in:
        # "Using the Output Embedding to Improve Language Models" (Press & Wolf 2016)
        # https://arxiv.org/abs/1608.05859
        # and
        # "Tying Word Vectors and Word Classifiers: A Loss Framework for Language Modeling" (Inan et al. 2016)
        # https://arxiv.org/abs/1611.01462
        if tie_weights:
            self.decoder.weight = self.encoder.weight

        self.init_weights(tie_weights)

        self.rnn_type = rnn_type
        self.ninp = ninp
        self.nhid = nhid
        self.nhidlast = nhidlast
        self.nlayers = nlayers
        self.dropout = dropout
        self.dropouti = dropouti
        self.dropouth = dropouth
        self.dropoute = dropoute
        self.ldropout = ldropout
        self.dropoutl = ldropout
        self.n_experts = n_experts
        self.ntoken = ntoken

        size = 0
        for p in self.parameters():
            size += p.nelement()
        print('param size: {}'.format(size))

    def init_weights(self, tie_weights):
        initrange = 0.1
        self.encoder.weight.data.uniform_(-initrange, initrange)
        self.encoder.weight.data[0,:] = 0
        self.decoder.bias.data.fill_(0)
        if tie_weights:
            self.decoder.weight.data.uniform_(-initrange, initrange)

    def forward(self, input, hidden, return_h=False, return_prob=False):
        batch_size = input.size(1)
        emb = embedded_dropout(self.encoder, input, dropout=self.dropoute if (self.training and self.use_dropout) else 0)
        emb = self.lockdrop(emb, self.dropouti if self.use_dropout else 0)
        raw_output = emb
        new_hidden = []
        raw_outputs = []
        outputs = []
        for l, rnn in enumerate(self.rnns):
            raw_output, new_h = rnn(raw_output, hidden[l])
            new_hidden.append(new_h)
            raw_outputs.append(raw_output)
            if l != self.nlayers - 1:
                raw_output = self.lockdrop(raw_output, self.dropouth if self.use_dropout else 0)
                outputs.append(raw_output)
        hidden = new_hidden

        output = self.lockdrop(raw_output, self.dropout if self.use_dropout else 0)
        outputs.append(output)

        latent = self.latent(output)
        latent = self.lockdrop(latent, self.dropoutl if self.use_dropout else 0)
        logit = self.decoder(latent.view(-1, self.ninp))

        prior_logit = self.prior(output).contiguous().view(-1, self.n_experts)
        prior = nn.functional.softmax(prior_logit, -1)

        prob = nn.functional.softmax(logit.view(-1, self.ntoken), -1).view(-1, self.n_experts, self.ntoken)
        prob = (prob * prior.unsqueeze(2).expand_as(prob)).sum(1)

        if return_prob:
            model_output = prob
        else:
            log_prob = torch.log(prob.add_(1e-8))
            model_output = log_prob

        model_output = model_output.view(-1, batch_size, self.ntoken)

        if return_h:
            return model_output, hidden, raw_outputs, outputs
        return model_output, hidden

    def init_hidden(self, bsz):
        weight = next(self.parameters()).data
        return [(Variable(weight.new(1, bsz, self.nhid if l != self.nlayers - 1 else self.nhidlast).zero_()),
                 Variable(weight.new(1, bsz, self.nhid if l != self.nlayers - 1 else self.nhidlast).zero_()))
                for l in range(self.nlayers)]

if __name__ == '__main__':
    model = RNNModel('LSTM', 10, 12, 12, 12, 2)
    input = Variable(torch.LongTensor(13, 9).random_(0, 10))
    hidden = model.init_hidden(9)
    model(input, hidden)
