--
-- User: pat
-- Date: 1/29/16
--

package.path = package.path .. ";src/?.lua"

require 'torch'
require 'rnn'
require 'optim'
require 'UniversalSchemaEncoder'
require 'nn-modules/ReplicateAs'
require 'nn-modules/ViewTable'
require 'nn-modules/VariableLengthConcatTable'

grad = require 'autograd'
grad.optimize(true) -- global


local UniversalSchemaRelationPool, parent = torch.class('UniversalSchemaRelationPool', 'UniversalSchemaEncoder')
local UniversalSchemaAttentionDot, _ = torch.class('UniversalSchemaAttentionDot', 'UniversalSchemaRelationPool')
local UniversalSchemaAttentionMatrix, _ = torch.class('UniversalSchemaAttentionMatrix', 'UniversalSchemaRelationPool')
local UniversalSchemaMean, _ = torch.class('UniversalSchemaMean', 'UniversalSchemaRelationPool')
local UniversalSchemaMax, _ = torch.class('UniversalSchemaMax', 'UniversalSchemaRelationPool')
local UniversalSchemaTopK, _ = torch.class('UniversalSchemaTopK', 'UniversalSchemaRelationPool')




--function UniversalSchemaRelationPool:__init(params, row_table, row_encoder, col_table, col_encoder, use_entities)
--    if params.relationPool and params.relationPool ~= '' then
--        col_encoder = relation_pool_encoder(params, col_encoder)
--    end
--    parent:__init(params, row_table, row_encoder, col_table, col_encoder, use_entities)
--end





local expand_as = function(input)
    local target_tensor = input[1]
    local orig_tensor = input[2]
    local expanded_tensor = torch.expand(orig_tensor, target_tensor:size())
    return expanded_tensor
end

local function make_attention(y_idx, hn_idx, dim)
    local term_1 = nn.Sequential():add(nn.SelectTable(y_idx)):add(nn.TemporalConvolution(dim, dim, 1))
    local term_2 = nn.Sequential()
        :add(nn.ConcatTable()
            :add(nn.SelectTable(y_idx))
            :add(nn.Sequential():add(nn.SelectTable(hn_idx)):add(nn.View(-1, 1, dim))))
        :add(grad.nn.AutoModule('AutoExpandAs')(expand_as)):add(nn.TemporalConvolution(dim, dim, 1))
    local concat = nn.ConcatTable():add(term_1):add(term_2)
    local M = nn.Sequential():add(concat):add(nn.CAddTable()):add(nn.Tanh())
    local alpha = nn.Sequential()
        :add(M):add(nn.TemporalConvolution(dim, 1, 1))
        :add(nn.SoftMax())
    local r = nn.Sequential():add(nn.ConcatTable():add(alpha):add(nn.SelectTable(y_idx)))
        :add(nn.MM(true)):add(nn.View(-1, dim))
    return r
end

-- given a row and a set of columns, return the dot products between the row and each column
local function score_all_relations(row_idx, col_idx, dim, mlp)
    local row = nn.Sequential():add(nn.SelectTable(row_idx)):add(nn.View(-1, 1, dim))
    local col = nn.Sequential():add(nn.SelectTable(col_idx))
    if mlp then
        row:add(nn.TemporalConvolution(dim, dim, 1))
--            :add(nn.ReLU())
--            :add(nn.TemporalConvolution(dim, dim, 1))
        col:add(nn.TemporalConvolution(dim, dim, 1))
--            :add(nn.ReLU())
--            :add(nn.TemporalConvolution(dim, dim, 1))
    end
    local relation_scorer = nn.Sequential()
        :add(nn.ConcatTable()
            :add(nn.Sequential()
                :add(nn.ConcatTable()
                    :add(nn.SelectTable(col_idx))
                    :add(row))
                :add(grad.nn.AutoModule('AutoExpandAs')(expand_as)))
        :add(col))
        :add(nn.CMulTable()):add(nn.Sum(3))
    return relation_scorer
end


function UniversalSchemaAttentionDot:build_scorer()
    local pos_score = nn.Sequential()
            :add(nn.ConcatTable()
            :add(make_attention(2, 1, self.params.colDim))
            :add(nn.SelectTable(1)))
            :add(nn.CMulTable()):add(nn.Sum(2))
    local neg_score = nn.Sequential()
            :add(nn.ConcatTable()
            :add(make_attention(2, 3, self.params.colDim))
            :add(nn.SelectTable(3)))
            :add(nn.CMulTable()):add(nn.Sum(2))

    local score_table = nn.ConcatTable()
        :add(pos_score):add(neg_score)
    return score_table
end

function UniversalSchemaAttentionMatrix:build_scorer()
    local pos_score = nn.Sequential():add(make_attention(2, 1, self.params.colDim)):add(nn.TemporalConvolution(self.params.colDim, 1, 1))
    local neg_score = nn.Sequential():add(make_attention(2, 3, self.params.colDim)):add(nn.TemporalConvolution(self.params.colDim, 1, 1))
    local score_table = nn.ConcatTable()
        :add(pos_score):add(neg_score)
    return score_table
end


function UniversalSchemaMean:build_scorer()
    local pos_score = score_all_relations(1, 2, self.params.colDim, self.params.mlp):add(nn.Mean(2))
    local neg_score = score_all_relations(3, 2, self.params.colDim, self.params.mlp):add(nn.Mean(2))
    local score_table = nn.ConcatTable()
        :add(pos_score):add(neg_score)
    return score_table
end

function UniversalSchemaMax:build_scorer()
    local pos_score = score_all_relations(1, 2, self.params.colDim, self.params.mlp):add(nn.Max(2))
    local neg_score = score_all_relations(3, 2, self.params.colDim, self.params.mlp):add(nn.Max(2))
    local score_table = nn.ConcatTable()
        :add(pos_score):add(neg_score)
    return score_table
end

function UniversalSchemaTopK:build_scorer()
    require 'nn-modules/TopK'
    local pos_score = score_all_relations(1, 2, self.params.colDim, self.params.mlp):add(nn.TopK(self.params.k, 2)):add(nn.Mean(2))
    local neg_score = score_all_relations(3, 2, self.params.colDim, self.params.mlp):add(nn.TopK(self.params.k, 2)):add(nn.Mean(2))
    local score_table = nn.ConcatTable()
        :add(pos_score):add(neg_score)
    return score_table
end


----- Evaluate ----

function UniversalSchemaRelationPool:score_subdata(sub_data)
    local batches = {}
    if sub_data.ep then self:gen_subdata_batches_four_col(sub_data, sub_data, batches, 0, false)
    else self:gen_subdata_batches_three_col(sub_data, sub_data, batches, 0, false) end

    local scores = {}
    for i = 1, #batches do
        local row_batch, col_batch, _ = unpack(batches[i].data)
        local encoded_row = self.row_encoder(row_batch):clone()
        local encoded_col = self.col_encoder(col_batch):clone()
        if encoded_col:dim() == 4 then encoded_col = encoded_col:view(encoded_col:size(1), encoded_col:size(2), encoded_col:size(4)) end
        local x = {encoded_row, encoded_col}
        local score = self.net:get(2):get(1)(x):clone()
        table.insert(scores, score)
    end

    return scores, sub_data.label:view(sub_data.label:size(1))
end
