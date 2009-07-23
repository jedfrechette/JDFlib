function trendPlunge = unit2tp(unitVec)
% Convert the orientation of a line, given as a  unit vector, to its
% orientation in terms of trend and plunge.
%
% trendPlunge = tp2unit(unitVec)

% Parameters:
%   unitVec = Array containing the x, y, and z values of the equivalent unit
%             vector in the 1st, 2nd, and 3rd columns respectively. (REQUIRED)
%
% Return:
%   trendPlunge  = Array containing trend and plunge values (degrees). The first
%                  column is the trend of a line projected on to a horizontal
%                  plane. Measured as degrees clockwize from north. The second
%                  column contains the plunge of a line relative to its
%                  projection on to a horizontal plane. Measured as a positive
%                  angle (degrees) downward from the horizontal plane.

% Author: Jed Frechette <jedfrechette@gmail.com>
% Date: 27 April 2006

x = unitVec(:, 1);
y = unitVec(:, 2);
z = unitVec(:, 3);

plunge = asin(z);


trendPlunge(:, 2) = rad2deg(plunge);
trendPlunge(:, 1) = rad2deg(asin(y ./ cos(plunge)));

negX = x < 0;
negY = y < 0;
negXY = x < 0 & y < 0;

trendPlunge(negX, 1) = 90 + trendPlunge(negX, 1);
trendPlunge(negY, 1) = 360 + trendPlunge(negY, 1);
trendPlunge(negXY, 1) = trendPlunge(negXY, 1) - 180;


