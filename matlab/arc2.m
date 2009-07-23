function arc2(r, az1, az2);
% arc2(r,az1, az2)
% This function draws an arc of a circle
% at a radius r from the origin, from
% az1 to az2 where these are azimuths in
% degrees measured from north
% differs from arc.m only in using dotted line
% Written by Gerry Middleton, December 1996

% modified by Mousumi Roy, UNM, to change edgecolor on arcs
% April 2006

azinc = 5;
az = [az1:azinc:az2];
len = length(az);
rs = zeros(len,1);
rc = zeros(len,1);
rs = r*sin(pi*az/180);
rc = r*cos(pi*az/180);
plot(rs, rc,'r:')