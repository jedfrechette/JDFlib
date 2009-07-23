function composite = sea(data, eAnchor, eLength, eOffset)
% Perform a superposed epoch analysis.
%
%   composite = sea(data, eAnchor, eLength, eOffset)
%
% Parameters:
%   data    = Two column array containing x values in the first column and y
%             values in the second column. The x values are assumed to be
%             evenly spaced. (REQUIRED)
%   eAnchor = Vector containing a list of x values that serve as anchors for
%             each epoch. (REQUIRED)
%   eLength = Scalar length of each epoch. (REQUIRED)
%   eOffset = Scalar offset of the first element of the epoch relative to
%             eAnchor. (DEFAULT = 0)
%
% Return:
%   composite = Two column array containing nondimensional offsets relative
%               to eAnchor in the first column and the mean value of y from all
%               epochs in the second column.

% Author: Jed Frechette <jedfrechette@gmail.com>
% Version: 0.1
% Date: 21 April 2006

% Check usage.
if nargin < 3 || nargin > 4
   usage("composite = sea(data, eAnchor, eLength, eOffset)")
end

if !isvector(eAnchor)
    error("The parameter eAnchor must be a vector.")
end

if columns(data) ~= 2
    error("The parameter data must have 2 columns.")
end

% Set default values
if nargin < 4, eOffset = 0; end

% Setup up array containing all epochs.
nEpoch = length(eAnchor);
epoch = zeros(eLength, nEpoch);
x = data(:, 1);
y = data(:, 2);

for ii = 1:nEpoch
    eStart = eAnchor(ii) + eOffset;
    eEnd = eStart + eLength -1;
    yIdx = (x >= eStart) & (x <= eEnd);
    epochArray(:, ii) = y(yIdx);
end

% Calculate the composite mean ignoring NaN values
composite(:, 1) = [eOffset:(eOffset + eLength - 1)]';
composite(:, 2) = nanmean(epochArray, 2);
