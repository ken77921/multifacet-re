-- http://stackoverflow.com/questions/36158058/torch-save-tensor-to-csv-file

require 'torch'

local cmd = torch.CmdLine()
cmd:option('-inFile', '', 'input torch embedding')
cmd:option('-outFile', '', 'output csv file')
cmd:option('-delim', ',', 'delimiter to break string on')

local params = cmd:parse(arg)

-- matrix = torch.load("/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/models/meta/uschema-english-relogged-50d/2016-09-30_22/15-rows") -- a 5x3 matrix
matrix = torch.load(params.inFile) -- a 5x3 matrix

print(matrix:size()) -- let's see the matrix content

-- subtensor = matrix[{{1,3}, {2,3}}] -- let's create a view on the row 1 to 3, for which we take columns 2 to 3 (the view is a 3x2 matrix, note that values are bound to the original tensor)
subtensor = matrix
--local out = assert(io.open("/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/models/meta/uschema-english-relogged-50d/2016-09-30_22/15-rows.csv", "w")) -- open a file for serialization
local out = assert(io.open(params.outFile, "w")) -- open a file for serialization

splitter = params.delim
for i=1,subtensor:size(1) do
    for j=1,subtensor:size(2) do
        out:write(subtensor[i][j])
        if j == subtensor:size(2) then
            out:write("\n")
        else
            out:write(splitter)
        end
    end
end

out:close()
