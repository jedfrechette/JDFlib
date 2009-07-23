function unitVec = tp2unit(trendPlunge)
% Convert the orientation of a line in terms of trend and plunge to a unit
% vector.
%
% unitVec = tp2unit(trendPlunge)
%
% Parameters:
%   trendPlunge  = Array containing trend and plunge values (degrees). The first
%                  column is the trend of a line projected on to a horizontal
%                  plane. Measured as degrees clockwize from north. The second
%                  column contains the plunge of a line relative to its
%                  projection on to a horizontal plane. Measured as a positive
%                  angle (degrees) downward from the horizontal plane.
%                  (REQUIRED)
%
% Return:
%   unitVec = Array containing the x, y, and z values of the equivalent unit
%             vector in the 1st, 2nd, and 3rd columns respectively.

% Author: Jed Frechette <jedfrechette@gmail.com>
% Date: 27 April 2006

trend = deg2rad(trendPlunge(:, 1));
plunge = deg2rad(trendPlunge(:, 2));

unitVec(:, 1) = cos(plunge) .* cos(trend);
unitVec(:, 2) = cos(plunge) .* sin(trend);
unitVec(:, 3) = sin(plunge);
