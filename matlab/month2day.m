function firstLastDay = month2day(month)
% Return the first and last day of a month as numbers starting at 1 on January
% 1 and ending at 366 on December 31.
%
% firstLastDay = month2day(month)
%
% Parameters:
%	month		= An array containing the month or months (1-12) that the first
%				  and last days would like to be known.
%
% Return:
%   firstLastDay = A 2 column array containing the first and last day
%				   (from 0-366) of the month that was specified as input.
%
% Author: Jed Frechette
% Date: 18 February 2006

for ii = 1:length(month)
	switch month(ii)
		case 1
			firstLastDay(ii, 1) = 1;
			firstLastDay(ii, 2) = 31;
		case 2
			firstLastDay(ii, 1) = 32;
			firstLastDay(ii, 2) = 60;
		case 3
			firstLastDay(ii, 1) = 61;
			firstLastDay(ii, 2) = 91;
		case 4
			firstLastDay(ii, 1) = 92;
			firstLastDay(ii, 2) = 121;
		case 5
			firstLastDay(ii, 1) = 122;
			firstLastDay(ii, 2) = 152;
		case 6
			firstLastDay(ii, 1) = 153;
			firstLastDay(ii, 2) = 182;
		case 7
			firstLastDay(ii, 1) = 183;
			firstLastDay(ii, 2) = 213;
		case 8
			firstLastDay(ii, 1) = 214;
			firstLastDay(ii, 2) = 244;
		case 9
			firstLastDay(ii, 1) = 245;
			firstLastDay(ii, 2) = 274;
		case 10
			firstLastDay(ii, 1) = 275;
			firstLastDay(ii, 2) = 305;
		case 11
			firstLastDay(ii, 1) = 306;
			firstLastDay(ii, 2) = 335;
		case 12
			firstLastDay(ii, 1) = 336;
			firstLastDay(ii, 2) = 366;
	end
end
