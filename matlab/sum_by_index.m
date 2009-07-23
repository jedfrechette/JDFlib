function outputMatrix = sum_by_index(inputMatrix)
% Load a 2 column matrix and sum all of the values in the second row that have
% the same index value in the first row.
%
% outputMatrix = sum_by_index(inputMatrix)
%
% Parameters:
%   inputMatrix     = An m by 2 matrix containing indexes in the first column
%                     and values in the second column. Any index may appear in
%                     multiple rows.
%
% Return:
%   outputMatrix    = An m by 3 matrix containing indexes in the first column,
%                     summed values in the second column, and the number of
%                     values summed in the third column.
%
% Author: Jed Frechette
% Date: 4 November 2005

% Find the minimum and maximum index values.
minI = min(inputMatrix(:, 1));
maxI = max(inputMatrix(:, 1));

outputMatrix = zeros(maxI - minI, 3);

% Identify indexes.
i = 1;
for index = minI:maxI
    [row, col] = find(inputMatrix == index);
    
    % Calculate the sum and the number of components.
    valueSum = 0;
    n = 0;
    for j = 1:length(row)
       valueSum = valueSum + inputMatrix(row(j), 2);
       n = n + 1;
    end

    % Store the index, the summed value, and the number of components in a
    % matrix.
    outputMatrix(i, 1) = index;
    outputMatrix(i, 2) = valueSum;
    outputMatrix(i, 3) = n;

    i = i + 1;
end
