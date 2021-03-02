-- http://stackoverflow.com/questions/36158058/torch-save-tensor-to-csv-file

require 'torch'

local cmd = torch.CmdLine()
cmd:option('-inFile', '', 'input csv file' )
cmd:option('-outFile', '', 'output torch embedding')

local params = cmd:parse(arg)


-- Read data from CSV to tensor
local csvFile = io.open(params.inFile, 'r')  
--local header = csvFile:read()

local count = 0  
for line in csvFile:lines('*l') do  
  count = count + 1
end
csvFile:close() 
emb_dim=20
ROWS=count


local data = torch.Tensor(ROWS, emb_dim)

local csvFile = io.open(params.inFile, 'r')  
local i = 0  
for line in csvFile:lines('*l') do  
  i = i + 1
  local l = line:split(',')
  for key, val in ipairs(l) do
    --print(key)
    --print(val)
    data[i][tonumber(key)] = tonumber(val)
  end
end

csvFile:close() 

torch.save(params.outFile,data)


