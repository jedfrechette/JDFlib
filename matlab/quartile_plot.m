%% Copyright (C) 2006 Jed Frechette
%%
%% This program is free software; you can redistribute it and/or modify
%% it under the terms of the GNU General Public License as published by
%% the Free Software Foundation; either version 2 of the License, or
%% (at your option) any later version.
%%
%% This program is distributed in the hope that it will be useful,
%% but WITHOUT ANY WARRANTY; without even the implied warranty of
%% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%% GNU General Public License for more details.
%%
%% You should have received a copy of the GNU General Public License
%% along with this program; if not, write to the Free Software
%% Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

%% usage: s = quartileplot (DATA, SYMBOL, VERTICAL, MAXWHISKER, LOCATION)
%%
%% The quartile plot is a graphical display that simultaneously describes
%% several important features of a data set, such as center, spread, departure
%% from symmetry, and identification of observations that lie unusually far
%% from the bulk of the data. It is a modification of the standard boxplot
%% that was first proposed by Edward Tufte in his book The Visual Display of
%% Quantitative Information.
%%
%% DATA is a matrix with one column for each dataset, or DATA is a cell
%% vector with one cell for each dataset.
%%
%% SYMBOL sets the symbol for the outlier values, default symbol for
%% points that lie outside 3 times the interquartile range is 'o',
%% default symbol for points between 1.5 and 3 times the interquartile
%% range is '+'. 
%% Examples
%% SYMBOL = '.'       points between 1.5 and 3 times the IQR is marked with
%%                    '.' and points outside 3 times IQR with 'o'.
%% SYMBOL = ['x','*'] points between 1.5 and 3 times the IQR is marked with
%%                    'x' and points outside 3 times IQR with '*'.
%%
%% VERTICAL = 0 makes the boxes horizontal, by default vertical = 1.
%%
%% MAXWHISKER defines the length of the whiskers as a function of the IQR
%% (default = 1.5). If maxwhisker = 0 then boxplot displays all data  
%% values outside the box using the plotting symbol for points that lie
%% outside 3 times the IQR.
%%
%% LOCATION is a vector with a length that is equal to the number of columns
%% in DATA. It defines the location of each quartile plot along the axis that
%% is not defined by the data set. The fist element of LOCATION corresponds to
%% location of the first column in DATA. The default is to place each quartile
%% plot on an integer starting with one.
%%
%% The returned matrix s has one column for each dataset as follows:
%%
%%    1  minimum
%%    2  1st quartile
%%    3  2nd quartile (median)
%%    4  3rd quartile
%%    5  maximum
%%    6  lower confidence limit for median
%%    7  upper confidence limit for median
%%
%% Example
%%
%%   title("Grade 3 heights");
%%   tics("x",1:2,["girls";"boys"]);
%%   axis([0,3]);
%%   quartileplot({randn(10,1)*5+140, randn(13,1)*8+135});
%%

%% Author: Jed Frechette <jedfrechette@gmail.com>
%% Version: .1
%% Created: 4 January 2006

function s = quartile_plot (data,symbol,vertical,maxwhisker,location)

%% Check usage
if nargin < 1 || nargin > 5
   usage("s = boxplot (data,notch,symbol,vertical,maxwhisker,location)")
end

%% figure out how many data sets we have
if iscell(data), 
  nc = length(data);
else
  if isvector(data), data = data(:); end
  nc = columns(data);
end

%% assign parameter defaults
if nargin < 5, location =[1:nc]; end
if nargin < 4, maxwhisker = 1.5; end
if nargin < 3, vertical = 1; end
if nargin < 3, symbol = ['+','o']; end

if rows(location) > 1
    location = location';
    if isvector(location) && (columns(location) == nc)
    else
        usage("The array LOCATION must be a vector with the same number...
 of elements as the array DATA has columns.")
    end
end
if length(symbol)==1, symbol(2)=symbol(1); end


%% compute statistics
%% s will contain
%%    1,5    min and max
%%    2,3,4  1st, 2nd and 3rd quartile
%%    6,7    lower and upper confidence intervals for median
s = zeros(7,nc);
box = zeros(1,nc);
whisker_x = ones(2,1)*[location,location];
whisker_y = zeros(2,2*nc);
outliers_x = [];
outliers_y = [];
outliers2_x = [];
outliers2_y = [];

for i=1:nc
  %% Get the next data set from the array or cell array
  if iscell(data)
    col = data{i}(:);
  else
    col = data(:,i);
  endif
  %% Skip missing data
  col(is_nan_or_na (col)) = [];
  %% Remember the data length
  nd = length(col);
  box(i) = nd;
  if (nd > 1)
    %% min,max and quartiles
    s(1:5,i) = statistics(col)(1:5);
    %% confidence interval for the median
    est = 1.57*(s(4,i)-s(2,i))/sqrt(nd);
    s(6,i) = max([s(3,i)-est, s(2,i)]);
    s(7,i) = min([s(3,i)+est, s(4,i)]);
    %% whiskers out to the last point within the desired inter-quartile range
    IQR = maxwhisker*(s(4,i)-s(2,i));
    whisker_y(:,i) = [min(col(col >= s(2,i)-IQR)); s(2,i)];
    whisker_y(:,nc+i) = [max(col(col <= s(4,i)+IQR)); s(4,i)];
    %% outliers beyond 1 and 2 inter-quartile ranges
    outliers = col((col < s(2,i)-IQR & col >= s(2,i)-2*IQR) | (col > s(4,i)+IQR & col <= s(4,i)+2*IQR));
    outliers2 = col(col < s(2,i)-2*IQR | col > s(4,i)+2*IQR);
    outliers_x = [outliers_x; location(i)*ones(size(outliers))];
    outliers_y = [outliers_y; outliers];
    outliers2_x = [outliers2_x; location(i)*ones(size(outliers2))];
    outliers2_y = [outliers2_y; outliers2];
  elseif (nd == 1)
    %% all statistics collapse to the value of the point
    s(:,i) = col;
    %% single point data sets are plotted as outliers.
    outliers_x = [outliers_x; i];
    outliers_y = [outliers_y; col];
  else
    %% no statistics if no points
    s(:,i) = NaN;
  end
end

%% Note which boxes don't have enough stats
chop = find(box <= 1);
    
%% Draw a solid line between the quartiles.
quartile_x = ones(2,1)*location;
quartile_y = s([2,4],:);

%% Draw a point at the median
median_x = whisker_x(1,1:nc);
median_y = s(3,:);

%% Chop all boxes which don't have enough stats
quartile_x(:,chop) = [];
quartile_y(:,chop) = [];
whisker_x(:,[chop,chop+nc]) = [];
whisker_y(:,[chop,chop+nc]) = [];
median_x(:,chop) = [];
median_y(:,chop) = [];

%quartile_x,quartile_y
%whisker_x,whisker_y
%median_x,median_y
%outliers2_x, outliers_y

%% Do the plot
if vertical
  plot (quartile_x, quartile_y, "b;;",
    whisker_x, whisker_y, "c;;",
	median_x, median_y, "@31");
    if isempty(outliers_x) != 0
    else
        hold on
	    plot(outliers_x, outliers_y, [symbol(1),"c;;"]); 
        hold off
    end
    if isempty(outliers2_x) != 0
    else
        hold on
        plot (outliers2_x, outliers2_y, [symbol(2),"c;;"]);
        hold off
    end
else
  plot (quartile_y, quartile_x, "b;;",
    whisker_y, whisker_x, "c;;",
	median_y, median_x, "@31");
    if isempty(outliers_x) != 0
        else
            hold on
	        plot(outliers_y, outliers_x, [symbol(1),"c;;"]);
            hold off
        end
    if isempty(outliers2_x) != 0
        else
            hold on
            plot (outliers2_y, outliers2_x, [symbol(2),"c;;"]);
            hold off
        end
endif

endfunction
