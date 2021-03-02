--
-- User: pat
-- Date: 9/1/15
--

require 'torch'
require 'optim'
require 'UniversalSchemaEncoder'

local TransEEncoder, parent = torch.class('TransEEncoder', 'UniversalSchemaEncoder')

function TransEEncoder:build_scorer()
    -- layers to compute score for the positive and negative samples
    local rel = nn.SelectTable(2)

    local pos_e1 = nn.Sequential():add(nn.SelectTable(1)):add(nn.SelectTable(1))
    local pos_e2 = nn.Sequential():add(nn.SelectTable(1)):add(nn.SelectTable(2))
    local pos_e1_rel = nn.Sequential():add(nn.ConcatTable():add(pos_e1):add(rel:clone())):add(nn.CAddTable())
    local pos_select = nn.ConcatTable():add(pos_e1_rel):add(pos_e2)
    local pos_score = nn.Sequential():add(pos_select):add(nn.PairwiseDistance(self.params.p))

    local neg_e1 = nn.Sequential():add(nn.SelectTable(3)):add(nn.SelectTable(1))
    local neg_e2 = nn.Sequential():add(nn.SelectTable(3)):add(nn.SelectTable(2))
    local neg_e1_rel = nn.Sequential():add(nn.ConcatTable():add(neg_e1):add(rel:clone())):add(nn.CAddTable())
    local neg_select = nn.ConcatTable():add(neg_e1_rel):add(neg_e2)
    local neg_score = nn.Sequential():add(neg_select):add(nn.PairwiseDistance(self.params.p))

    local score_table = nn.ConcatTable()
        :add(pos_score):add(neg_score)

    return score_table
end

function TransEEncoder:score_subdata(sub_data)
    local batches = {}
    if sub_data.ep then self:gen_subdata_batches_four_col(sub_data, sub_data, batches, 0, false)
    else self:gen_subdata_batches_three_col(sub_data, sub_data, batches, 0, false) end

    local scores = {}
    for i = 1, #batches do
        local row_batch, col_batch, _ = unpack(batches[i].data)
        if self.params.colEncoder == 'lookup-table' then col_batch = col_batch:view(col_batch:size(1), 1) end
        if self.params.rowEncoder == 'lookup-table' then row_batch = row_batch:view(row_batch:size(1), 1) end
        local encoded_rel = self.col_encoder(self:to_cuda(col_batch)):squeeze():clone()
        local encoded_ep = self.row_encoder(self:to_cuda(row_batch))
        local score = self:to_cuda(nn.PairwiseDistance(self.params.p))({encoded_ep[1] + encoded_rel, encoded_ep[2]})
        table.insert(scores, score)
    end
    return scores, sub_data.label:view(sub_data.label:size(1))
end

