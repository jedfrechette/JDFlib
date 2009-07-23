function [xArray, yArray] = euler(yp, deltaX, xSpan, y0)
% Approximate the solution to a differential equation using the Euler Method.
% If the function identified by the string f is in the form yp(x, y) the forward
% Euler Method will be used. If the function is in the form
% yp(x + deltaX, y(x + deltaX)) the reverse Euler Method is used.
%
% [xArray, yArray] = euler(yp, deltaX, xSpan, y0)
%
% Parameters:
%   yp          = A string containing the name of a function that is equal to
%                 the derivative y' = dy/dx (Required).
%   deltaX      = Step size to use (Required).
%   xSpan       = An array containing the initial and final values of x
%                 (Required).
%   y0          = The initial value of y (Required).
%
% Return:
%   xArray      = An array containing the values of x.
%   yArray      = An array containing the values of y.
%
% Author: Jed Frechette
% Date: 7 October 2005

% Set the initial and final values of x.
x0 = xSpan(1);
xN = xSpan(2);

% Calculate the required number of steps.
steps = ceil((xN - x0)/deltaX);

% Initialize arrays to store the results. 
xArray = zeros(1, steps + 1);
xArray(1, 1) =  x0;

yArray = zeros(1, steps + 1);
yArray(1,1) = y0;

% Perform Euler's Method to generate the numerical estimate.
for i = 1:steps
    yArray(i + 1) = yArray(i) + deltaX * feval(yp, xArray(i), yArray(i), deltaX);
    xArray(i + 1) = xArray(i) + deltaX;
end

xArray = xArray';
yArray = yArray';
