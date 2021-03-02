--input_model_path = "/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/models/meta/lstm-bi-maxpool-paper_USchema_init_50d_pub_seq_rel_dis_g2d/2017-04-04_14/15-model"
--output_file_path = "/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/models/meta/lstm-bi-maxpool-paper_USchema_init_50d_pub_seq_rel_dis_g2d/2017-04-04_14/15-col_tok"
input_model_path = "/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/models/meta/lstm-bi-maxpool-paper_50d_pub_seq_rel_lcc_org_g2g_tok20_word2vec/2017-04-20_11/15-model"
output_file_path = "/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/models/meta/lstm-bi-maxpool-paper_50d_pub_seq_rel_lcc_org_g2g_tok20_word2vec/2017-04-20_11/15-col_tok"

package.path = package.path .. ";src/?.lua;src/nn-modules/?.lua;src/eval/?.lua;src/classifier/?.lua;"

require 'torch'
require 'rnn'
require 'nn_modules_init'

model=torch.load(input_model_path)

tok_size=model.col_encoder.modules[1].weight:size()[1]
index=torch.range(1,tok_size)
token_emb=model.col_encoder:forward(index:view(tok_size,1))

torch.save(output_file_path,token_emb)
