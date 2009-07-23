% Script Snetplot
% Plots points on a Schmidt net created by schmidt.m
% Matrix of dips and azimuths is first loaded using matfile
% linetype must be inside single quotes, e.g. '+y'

% modified by M. Roy (April 2006) to eliminate call to matfile and user
% input

% help Snetplot
% X = matfile;
theta = pi*(90-X(:,2))/180;      %az converted to MATLAB angle
rho = sqrt(2)*sin(pi*(90-X(:,1))/360);   %projected distance from origin
xp = rho .* cos(theta);
yp = rho .* sin(theta);
%i = input('Type in linetype (e.g., +y, enclosed by quotes) for plot: ');
%plot(xp,yp,i);
plot(xp,yp,'+k');
