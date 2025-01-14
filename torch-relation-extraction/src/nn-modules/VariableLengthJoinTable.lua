local VariableLengthJoinTable, parent = torch.class('nn.VariableLengthJoinTable', 'nn.Module')

function VariableLengthJoinTable:__init(dimension, nInputDims)
   parent.__init(self)
   self.size = torch.LongStorage()
   self.dimension = dimension
   self.gradInput = {}
   self.nInputDims = nInputDims
end

function VariableLengthJoinTable:updateOutput(input)
   local dimension = self.dimension
   if self.nInputDims and input[1]:dim()==(self.nInputDims+1) then
       dimension = dimension + 1
   end

   for i=1,#input do
      local currentOutput = input[i]
      if i == 1 then
         self.size:resize(currentOutput:dim()):copy(currentOutput:size())
      else
         self.size[dimension] = self.size[dimension]
            + currentOutput:size(dimension)
      end
   end
   self.output:resize(self.size)

   local offset = 1
   for i=1,#input do
      local currentOutput = input[i]
      self.output:narrow(dimension, offset,
         currentOutput:size(dimension)):copy(currentOutput)
      offset = offset + currentOutput:size(dimension)
   end
   return self.output
end

function VariableLengthJoinTable:updateGradInput(input, gradOutput)
   local dimension = self.dimension
   if self.nInputDims and input[1]:dim()==(self.nInputDims+1) then
       dimension = dimension + 1
   end

   for i=1,#input do
      if self.gradInput[i] == nil then
         self.gradInput[i] = input[i].new()
      end
      self.gradInput[i]:resizeAs(input[i])
   end

   -- clear out invalid gradInputs
   for i=#input+1, #self.gradInput do
      self.gradInput[i] = nil
   end

   local offset = 1
   for i=1,#input do
      local currentOutput = input[i]
      local currentGradInput = gradOutput:narrow(dimension, offset,
                      currentOutput:size(dimension))
      self.gradInput[i]:copy(currentGradInput)
      offset = offset + currentOutput:size(dimension)
   end
   return self.gradInput
end

function VariableLengthJoinTable:type(type)
   self.gradInput = {}
   return parent.type(self, type)
end
