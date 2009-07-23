function [meanDailyClimate, labels] = load_daily_climate_means(sourceFile)
% Import a data file containing mean daily climatic values for 1 year (366
% days). Data is in the format available for individual stations from
% http://www.wrcc.dri.edu. Day 366 must be on the last line of the file and the
% columns are arranged in the same order as the return values listed below.
% Columns are seperated by white space.
%
% [meanDailyClimate, labels] = load_daily_climate_means(sourceFile)
%
% Parameters:
%   sourceFile  = String containing the name of a file to import.
%
% Return:
%   meanDailyClimate    = Array containing mean daily climatic data.
%   labels              = Array containg column labels. The labels are
%                         described below.
%
%   dayYear     = Day of year.
%   month       = Month.
%   dayMonth    = Day of Month.
%   maxT        = Maximum temperature (degrees C).
%   nMaxT       = Number of years used to calculate mean max temp.
%   minT        = Minimum temperature (degrees C).
%   nMinT       = Number of years used to calculate mean min temp.
%   precip      = Precipitation (mm).
%   nPrecip     = Number of years used to calculate mean precipitation.
%   sdMaxT      = Maximum temperature standard deviation.
%   sdMinT      = Minimum temperature standard deviation.
%
% Author: Jed Frechette
% Date: 23 October 2005

% Trim the header then create and load the temporary file.
system(['tail -n 366 ', sourceFile, '> /tmp/temp.dat']);
load /tmp/temp.dat;

% Create array containing column labels.
labels = ['dayYear'; 'month'; 'dayMonth'; 'maxT'; 'nMaxT'; 'minT'; 'nMinT';...
          'precip'; 'nPrecip'; 'sdMaxT'; 'sdMinT'];
          
% Convert data to metric units.
temp(:, 4)  = (5 * (temp(:, 4) - 32)) / 9;
temp(:, 6)  = (5 * (temp(:, 6) - 32)) / 9;
temp(:, 10) = (5 * (temp(:, 10) - 32)) / 9;
temp(:, 11) = (5 * (temp(:, 11) - 32)) / 9;
temp(:, 8)  = 25.4 * temp(:, 8);

% Assign data to climate matrix.
meanDailyClimate = temp;

% Cleanup temporary file.
system('rm /tmp/temp.dat');
