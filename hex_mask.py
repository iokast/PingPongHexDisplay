import numpy as np

hex_mask = [
[None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,1,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,0,None,None,None,2,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,8,None,None,None,6,None,None,None,4,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,9,None,None,None,7,None,None,None,5,None,None,None,3,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,None,None,11,None,None,None,13,None,None,None,15,None,None,None,17,None,None,None,19,None,None,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,10,None,None,None,12,None,None,None,14,None,None,None,16,None,None,None,18,None,None,None,20,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,34,None,None,None,32,None,None,None,30,None,None,None,28,None,None,None,26,None,None,None,24,None,None,None,22,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,35,None,None,None,33,None,None,None,31,None,None,None,29,None,None,None,27,None,None,None,25,None,None,None,23,None,None,None,21,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,37,None,None,None,39,None,None,None,41,None,None,None,43,None,None,None,45,None,None,None,47,None,None,None,49,None,None,None,51,None,None,None,53,None,None,None,None,None,None,],
[None,None,None,None,36,None,None,None,38,None,None,None,40,None,None,None,42,None,None,None,44,None,None,None,46,None,None,None,48,None,None,None,50,None,None,None,52,None,None,None,54,None,None,None,None,],
[None,None,76,None,None,None,74,None,None,None,72,None,None,None,70,None,None,None,68,None,None,None,66,None,None,None,64,None,None,None,62,None,None,None,60,None,None,None,58,None,None,None,56,None,None,],
[77,None,None,None,75,None,None,None,73,None,None,None,71,None,None,None,69,None,None,None,67,None,None,None,65,None,None,None,63,None,None,None,61,None,None,None,59,None,None,None,57,None,None,None,55,],
[None,None,79,None,None,None,81,None,None,None,83,None,None,None,85,None,None,None,87,None,None,None,89,None,None,None,91,None,None,None,93,None,None,None,95,None,None,None,97,None,None,None,99,None,None,],
[78,None,None,None,80,None,None,None,82,None,None,None,84,None,None,None,86,None,None,None,88,None,None,None,90,None,None,None,92,None,None,None,94,None,None,None,96,None,None,None,98,None,None,None,100,],
[None,None,122,None,None,None,120,None,None,None,118,None,None,None,116,None,None,None,114,None,None,None,112,None,None,None,110,None,None,None,108,None,None,None,106,None,None,None,104,None,None,None,102,None,None,],
[123,None,None,None,121,None,None,None,119,None,None,None,117,None,None,None,115,None,None,None,113,None,None,None,111,None,None,None,109,None,None,None,107,None,None,None,105,None,None,None,103,None,None,None,101,],
[None,None,125,None,None,None,127,None,None,None,129,None,None,None,131,None,None,None,133,None,None,None,135,None,None,None,137,None,None,None,139,None,None,None,141,None,None,None,143,None,None,None,145,None,None,],
[124,None,None,None,126,None,None,None,128,None,None,None,130,None,None,None,132,None,None,None,134,None,None,None,136,None,None,None,138,None,None,None,140,None,None,None,142,None,None,None,144,None,None,None,146,],
[None,None,168,None,None,None,166,None,None,None,164,None,None,None,162,None,None,None,160,None,None,None,158,None,None,None,156,None,None,None,154,None,None,None,152,None,None,None,150,None,None,None,148,None,None,],
[169,None,None,None,167,None,None,None,165,None,None,None,163,None,None,None,161,None,None,None,159,None,None,None,157,None,None,None,155,None,None,None,153,None,None,None,151,None,None,None,149,None,None,None,147,],
[None,None,171,None,None,None,173,None,None,None,175,None,None,None,177,None,None,None,179,None,None,None,181,None,None,None,183,None,None,None,185,None,None,None,187,None,None,None,189,None,None,None,191,None,None,],
[170,None,None,None,172,None,None,None,174,None,None,None,176,None,None,None,178,None,None,None,180,None,None,None,182,None,None,None,184,None,None,None,186,None,None,None,188,None,None,None,190,None,None,None,192,],
[None,None,214,None,None,None,212,None,None,None,210,None,None,None,208,None,None,None,206,None,None,None,204,None,None,None,202,None,None,None,200,None,None,None,198,None,None,None,196,None,None,None,194,None,None,],
[215,None,None,None,213,None,None,None,211,None,None,None,209,None,None,None,207,None,None,None,205,None,None,None,203,None,None,None,201,None,None,None,199,None,None,None,197,None,None,None,195,None,None,None,193,],
[None,None,217,None,None,None,219,None,None,None,221,None,None,None,223,None,None,None,225,None,None,None,227,None,None,None,229,None,None,None,231,None,None,None,233,None,None,None,235,None,None,None,237,None,None,],
[216,None,None,None,218,None,None,None,220,None,None,None,222,None,None,None,224,None,None,None,226,None,None,None,228,None,None,None,230,None,None,None,232,None,None,None,234,None,None,None,236,None,None,None,238,],
[None,None,260,None,None,None,258,None,None,None,256,None,None,None,254,None,None,None,252,None,None,None,250,None,None,None,248,None,None,None,246,None,None,None,244,None,None,None,242,None,None,None,240,None,None,],
[261,None,None,None,259,None,None,None,257,None,None,None,255,None,None,None,253,None,None,None,251,None,None,None,249,None,None,None,247,None,None,None,245,None,None,None,243,None,None,None,241,None,None,None,239,],
[None,None,263,None,None,None,265,None,None,None,267,None,None,None,269,None,None,None,271,None,None,None,273,None,None,None,275,None,None,None,277,None,None,None,279,None,None,None,281,None,None,None,283,None,None,],
[262,None,None,None,264,None,None,None,266,None,None,None,268,None,None,None,270,None,None,None,272,None,None,None,274,None,None,None,276,None,None,None,278,None,None,None,280,None,None,None,282,None,None,None,284,],
[None,None,306,None,None,None,304,None,None,None,302,None,None,None,300,None,None,None,298,None,None,None,296,None,None,None,294,None,None,None,292,None,None,None,290,None,None,None,288,None,None,None,286,None,None,],
[307,None,None,None,305,None,None,None,303,None,None,None,301,None,None,None,299,None,None,None,297,None,None,None,295,None,None,None,293,None,None,None,291,None,None,None,289,None,None,None,287,None,None,None,285,],
[None,None,309,None,None,None,311,None,None,None,313,None,None,None,315,None,None,None,317,None,None,None,319,None,None,None,321,None,None,None,323,None,None,None,325,None,None,None,327,None,None,None,329,None,None,],
[308,None,None,None,310,None,None,None,312,None,None,None,314,None,None,None,316,None,None,None,318,None,None,None,320,None,None,None,322,None,None,None,324,None,None,None,326,None,None,None,328,None,None,None,330,],
[None,None,351,None,None,None,349,None,None,None,347,None,None,None,345,None,None,None,343,None,None,None,341,None,None,None,339,None,None,None,337,None,None,None,335,None,None,None,333,None,None,None,331,None,None,],
[None,None,None,None,350,None,None,None,348,None,None,None,346,None,None,None,344,None,None,None,342,None,None,None,340,None,None,None,338,None,None,None,336,None,None,None,334,None,None,None,332,None,None,None,None,],
[None,None,None,None,None,None,352,None,None,None,354,None,None,None,356,None,None,None,358,None,None,None,360,None,None,None,362,None,None,None,364,None,None,None,366,None,None,None,368,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,353,None,None,None,355,None,None,None,357,None,None,None,359,None,None,None,361,None,None,None,363,None,None,None,365,None,None,None,367,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,381,None,None,None,379,None,None,None,377,None,None,None,375,None,None,None,373,None,None,None,371,None,None,None,369,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,380,None,None,None,378,None,None,None,376,None,None,None,374,None,None,None,372,None,None,None,370,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,None,None,382,None,None,None,384,None,None,None,386,None,None,None,388,None,None,None,390,None,None,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,383,None,None,None,385,None,None,None,387,None,None,None,389,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,395,None,None,None,393,None,None,None,391,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,394,None,None,None,392,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,],
[None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,396,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,],]

digits_slant = np.array( [[[1, 1, 1],
                     [1, 0, 1],
                     [1, 0, 1],
                     [1, 0, 1],
                     [1, 1, 1]],

                    [[1, 1, 0],
                     [0, 1, 0],
                     [0, 1, 0],
                     [0, 1, 0],
                     [1, 1, 1]],

                    [[1, 1, 1],
                     [0, 0, 1],
                     [1, 1, 1],
                     [1, 0, 0],
                     [1, 1, 1]],

                    [[1, 1, 1],
                     [0, 0, 1],
                     [1, 1, 1],
                     [0, 0, 1],
                     [1, 1, 1]],

                    [[1, 0, 1],
                     [1, 0, 1],
                     [1, 1, 1],
                     [0, 0, 1],
                     [0, 0, 1]],

                    [[1, 1, 1],
                     [1, 0, 0],
                     [1, 1, 1],
                     [0, 0, 1],
                     [1, 1, 1]],

                    [[1, 1, 1],
                     [1, 0, 0],
                     [1, 1, 1],
                     [1, 0, 1],
                     [1, 1, 1]],

                    [[1, 1, 1],
                     [0, 0, 1],
                     [0, 0, 1],
                     [0, 0, 1],
                     [0, 0, 1]],

                    [[1, 1, 1],
                     [1, 0, 1],
                     [1, 1, 1],
                     [1, 0, 1],
                     [1, 1, 1]],

                    [[1, 1, 1],
                     [1, 0, 1],
                     [1, 1, 1],
                     [0, 0, 1],
                     [1, 1, 1]]])

digits = np.array( 
                   [[[1, 1, 1], # 0
                     [1, 0, 1],
                     [1, 0, 1],
                     [1, 0, 1],
                     [0, 1, 0]],
                    
                    [[1, 1, 0], # 1
                     [0, 1, 0],
                     [0, 1, 0],
                     [1, 1, 1],
                     [0, 0, 0]],

                    [[1, 1, 1], #2
                     [0, 0, 1],
                     [1, 1, 0],
                     [1, 1, 1],
                     [0, 0, 0]],

                    [[1, 1, 1], # 3
                     [0, 0, 1],
                     [0, 1, 1],
                     [1, 0, 1],
                     [0, 1, 0]],

                    [[1, 0, 1], # 4
                     [1, 0, 1],
                     [0, 1, 1],
                     [0, 0, 1],
                     [0, 0, 0]],

                    [[1, 0, 1], # 5
                     [1, 1, 0],
                     [0, 1, 1],
                     [1, 0, 1],
                     [0, 1, 0]],

                    [[1, 1, 1], # 6
                     [1, 0, 0],
                     [1, 1, 1],
                     [1, 0, 1],
                     [0, 1, 0]],

                    [[1, 0, 1], # 7
                     [1, 1, 1],
                     [0, 0, 1],
                     [0, 0, 1],
                     [0, 0, 0]],

                    [[1, 1, 1], # 8
                     [1, 0, 1],
                     [1, 1, 1],
                     [1, 0, 1],
                     [0, 1, 0]],

                    [[1, 1, 1], # 9
                     [1, 0, 1],
                     [0, 1, 1],
                     [1, 0, 1],
                     [0, 1, 0]]])

clock_positions_slant = np.array([[[74,38,39],
                             [81,73,72],
                             [120,82,83],
                             [127,119,118],
                             [166,128,129]],

                            [[32,12,13],
                            [41,31,30],
                            [70,42,43],
                            [85,69,68],
                            [116,86,87]],

                            [[17,18,24],
                            [26,25,49],
                            [47,48,62],
                            [64,63,93],
                            [91,92,108]],

                            [[51,52,58],
                            [60,59,97],
                            [95,96,104],
                            [106,105,143],
                            [141,142,150]]])

clock_positions = np.array([
                           [[74,38,72],		
                            [81,73,83],		
                            [120,82,118],		
                            [127,119,129],		
                            [0,128,0]],		
                                    
                            [[70,42,68],		
                            [85,69,87],		
                            [116,86,114],		
                            [131,115,133],		
                            [0, 132,0]],		
                                    
                            [[64,48,62],		
                            [91,63,93],		
                            [110,92,108],		
                            [137,109,139],		
                            [0, 138, 0]],		
                                    
                            [[60,52,58],		
                            [95,59,97],		
                            [106,96,104],		
                            [141,105,143],		
                            [0, 142, 0]]])
                            
cartesian_coords = np.array([[0.5,8.6605],[0,9.52655],[0.5,10.3926],[1.5,12.1247],[1,11.25865],[1.5,10.3926],[1,9.52655],[1.5,8.6605],[1,7.79445],[1.5,6.9284],[2.5,5.1963],[2,6.06235],[2.5,6.9284],[2,7.79445],[2.5,8.6605],[2,9.52655],[2.5,10.3926],[2,11.25865],[2.5,12.1247],[2,12.99075],[2.5,13.8568],[3.5,15.5889],[3,14.72285],[3.5,13.8568],[3,12.99075],[3.5,12.1247],[3,11.25865],[3.5,10.3926],[3,9.52655],[3.5,8.6605],[3,7.79445],[3.5,6.9284],[3,6.06235],[3.5,5.1963],[3,4.33025],[3.5,3.4642],[4.5,1.7321],[4,2.59815],[4.5,3.4642],[4,4.33025],[4.5,5.1963],[4,6.06235],[4.5,6.9284],[4,7.79445],[4.5,8.6605],[4,9.52655],[4.5,10.3926],[4,11.25865],[4.5,12.1247],[4,12.99075],[4.5,13.8568],[4,14.72285],[4.5,15.5889],[4,16.45495],[4.5,17.321],[5.5,19.0531],[5,18.18705],[5.5,17.321],[5,16.45495],[5.5,15.5889],[5,14.72285],[5.5,13.8568],[5,12.99075],[5.5,12.1247],[5,11.25865],[5.5,10.3926],[5,9.52655],[5.5,8.6605],[5,7.79445],[5.5,6.9284],[5,6.06235],[5.5,5.1963],[5,4.33025],[5.5,3.4642],[5,2.59815],[5.5,1.7321],[5,0.86605],[5.5,0],[6.5,0],[6,0.86605],[6.5,1.7321],[6,2.59815],[6.5,3.4642],[6,4.33025],[6.5,5.1963],[6,6.06235],[6.5,6.9284],[6,7.79445],[6.5,8.6605],[6,9.52655],[6.5,10.3926],[6,11.25865],[6.5,12.1247],[6,12.99075],[6.5,13.8568],[6,14.72285],[6.5,15.5889],[6,16.45495],[6.5,17.321],[6,18.18705],[6.5,19.0531],[7.5,19.0531],[7,18.18705],[7.5,17.321],[7,16.45495],[7.5,15.5889],[7,14.72285],[7.5,13.8568],[7,12.99075],[7.5,12.1247],[7,11.25865],[7.5,10.3926],[7,9.52655],[7.5,8.6605],[7,7.79445],[7.5,6.9284],[7,6.06235],[7.5,5.1963],[7,4.33025],[7.5,3.4642],[7,2.59815],[7.5,1.7321],[7,0.86605],[7.5,0],[8.5,0],[8,0.86605],[8.5,1.7321],[8,2.59815],[8.5,3.4642],[8,4.33025],[8.5,5.1963],[8,6.06235],[8.5,6.9284],[8,7.79445],[8.5,8.6605],[8,9.52655],[8.5,10.3926],[8,11.25865],[8.5,12.1247],[8,12.99075],[8.5,13.8568],[8,14.72285],[8.5,15.5889],[8,16.45495],[8.5,17.321],[8,18.18705],[8.5,19.0531],[9.5,19.0531],[9,18.18705],[9.5,17.321],[9,16.45495],[9.5,15.5889],[9,14.72285],[9.5,13.8568],[9,12.99075],[9.5,12.1247],[9,11.25865],[9.5,10.3926],[9,9.52655],[9.5,8.6605],[9,7.79445],[9.5,6.9284],[9,6.06235],[9.5,5.1963],[9,4.33025],[9.5,3.4642],[9,2.59815],[9.5,1.7321],[9,0.86605],[9.5,0],[10.5,0],[10,0.86605],[10.5,1.7321],[10,2.59815],[10.5,3.4642],[10,4.33025],[10.5,5.1963],[10,6.06235],[10.5,6.9284],[10,7.79445],[10.5,8.6605],[10,9.52655],[10.5,10.3926],[10,11.25865],[10.5,12.1247],[10,12.99075],[10.5,13.8568],[10,14.72285],[10.5,15.5889],[10,16.45495],[10.5,17.321],[10,18.18705],[10.5,19.0531],[11.5,19.0531],[11,18.18705],[11.5,17.321],[11,16.45495],[11.5,15.5889],[11,14.72285],[11.5,13.8568],[11,12.99075],[11.5,12.1247],[11,11.25865],[11.5,10.3926],[11,9.52655],[11.5,8.6605],[11,7.79445],[11.5,6.9284],[11,6.06235],[11.5,5.1963],[11,4.33025],[11.5,3.4642],[11,2.59815],[11.5,1.7321],[11,0.86605],[11.5,0],[12.5,0],[12,0.86605],[12.5,1.7321],[12,2.59815],[12.5,3.4642],[12,4.33025],[12.5,5.1963],[12,6.06235],[12.5,6.9284],[12,7.79445],[12.5,8.6605],[12,9.52655],[12.5,10.3926],[12,11.25865],[12.5,12.1247],[12,12.99075],[12.5,13.8568],[12,14.72285],[12.5,15.5889],[12,16.45495],[12.5,17.321],[12,18.18705],[12.5,19.0531],[13.5,19.0531],[13,18.18705],[13.5,17.321],[13,16.45495],[13.5,15.5889],[13,14.72285],[13.5,13.8568],[13,12.99075],[13.5,12.1247],[13,11.25865],[13.5,10.3926],[13,9.52655],[13.5,8.6605],[13,7.79445],[13.5,6.9284],[13,6.06235],[13.5,5.1963],[13,4.33025],[13.5,3.4642],[13,2.59815],[13.5,1.7321],[13,0.86605],[13.5,0],[14.5,0],[14,0.86605],[14.5,1.7321],[14,2.59815],[14.5,3.4642],[14,4.33025],[14.5,5.1963],[14,6.06235],[14.5,6.9284],[14,7.79445],[14.5,8.6605],[14,9.52655],[14.5,10.3926],[14,11.25865],[14.5,12.1247],[14,12.99075],[14.5,13.8568],[14,14.72285],[14.5,15.5889],[14,16.45495],[14.5,17.321],[14,18.18705],[14.5,19.0531],[15.5,19.0531],[15,18.18705],[15.5,17.321],[15,16.45495],[15.5,15.5889],[15,14.72285],[15.5,13.8568],[15,12.99075],[15.5,12.1247],[15,11.25865],[15.5,10.3926],[15,9.52655],[15.5,8.6605],[15,7.79445],[15.5,6.9284],[15,6.06235],[15.5,5.1963],[15,4.33025],[15.5,3.4642],[15,2.59815],[15.5,1.7321],[15,0.86605],[15.5,0],[16.5,0],[16,0.86605],[16.5,1.7321],[16,2.59815],[16.5,3.4642],[16,4.33025],[16.5,5.1963],[16,6.06235],[16.5,6.9284],[16,7.79445],[16.5,8.6605],[16,9.52655],[16.5,10.3926],[16,11.25865],[16.5,12.1247],[16,12.99075],[16.5,13.8568],[16,14.72285],[16.5,15.5889],[16,16.45495],[16.5,17.321],[16,18.18705],[16.5,19.0531],[17,18.18705],[17.5,17.321],[17,16.45495],[17.5,15.5889],[17,14.72285],[17.5,13.8568],[17,12.99075],[17.5,12.1247],[17,11.25865],[17.5,10.3926],[17,9.52655],[17.5,8.6605],[17,7.79445],[17.5,6.9284],[17,6.06235],[17.5,5.1963],[17,4.33025],[17.5,3.4642],[17,2.59815],[17.5,1.7321],[17,0.86605],[18,2.59815],[18.5,3.4642],[18,4.33025],[18.5,5.1963],[18,6.06235],[18.5,6.9284],[18,7.79445],[18.5,8.6605],[18,9.52655],[18.5,10.3926],[18,11.25865],[18.5,12.1247],[18,12.99075],[18.5,13.8568],[18,14.72285],[18.5,15.5889],[18,16.45495],[19,14.72285],[19.5,13.8568],[19,12.99075],[19.5,12.1247],[19,11.25865],[19.5,10.3926],[19,9.52655],[19.5,8.6605],[19,7.79445],[19.5,6.9284],[19,6.06235],[19.5,5.1963],[19,4.33025],[20,6.06235],[20.5,6.9284],[20,7.79445],[20.5,8.6605],[20,9.52655],[20.5,10.3926],[20,11.25865],[20.5,12.1247],[20,12.99075],[21,11.25865],[21.5,10.3926],[21,9.52655],[21.5,8.6605],[21,7.79445],[22,9.52655]])
cube_coords = np.array([[-1,-10,11],[0,-11,11],[1,-11,10],[3,-11,8],[2,-11,9],[1,-10,9],[0,-10,10],[-1,-9,10],[-2,-9,11],[-3,-8,11],[-5,-6,11],[-4,-7,11],[-3,-7,10],[-2,-8,10],[-1,-8,9],[0,-9,9],[1,-9,8],[2,-10,8],[3,-10,7],[4,-11,7],[5,-11,6],[7,-11,4],[6,-11,5],[5,-10,5],[4,-10,6],[3,-9,6],[2,-9,7],[1,-8,7],[0,-8,8],[-1,-7,8],[-2,-7,9],[-3,-6,9],[-4,-6,10],[-5,-5,10],[-6,-5,11],[-7,-4,11],[-9,-2,11],[-8,-3,11],[-7,-3,10],[-6,-4,10],[-5,-4,9],[-4,-5,9],[-3,-5,8],[-2,-6,8],[-1,-6,7],[0,-7,7],[1,-7,6],[2,-8,6],[3,-8,5],[4,-9,5],[5,-9,4],[6,-10,4],[7,-10,3],[8,-11,3],[9,-11,2],[11,-11,0],[10,-11,1],[9,-10,1],[8,-10,2],[7,-9,2],[6,-9,3],[5,-8,3],[4,-8,4],[3,-7,4],[2,-7,5],[1,-6,5],[0,-6,6],[-1,-5,6],[-2,-5,7],[-3,-4,7],[-4,-4,8],[-5,-3,8],[-6,-3,9],[-7,-2,9],[-8,-2,10],[-9,-1,10],[-10,-1,11],[-11,0,11],[-11,1,10],[-10,0,10],[-9,0,9],[-8,-1,9],[-7,-1,8],[-6,-2,8],[-5,-2,7],[-4,-3,7],[-3,-3,6],[-2,-4,6],[-1,-4,5],[0,-5,5],[1,-5,4],[2,-6,4],[3,-6,3],[4,-7,3],[5,-7,2],[6,-8,2],[7,-8,1],[8,-9,1],[9,-9,0],[10,-10,0],[11,-10,-1],[11,-9,-2],[10,-9,-1],[9,-8,-1],[8,-8,0],[7,-7,0],[6,-7,1],[5,-6,1],[4,-6,2],[3,-5,2],[2,-5,3],[1,-4,3],[0,-4,4],[-1,-3,4],[-2,-3,5],[-3,-2,5],[-4,-2,6],[-5,-1,6],[-6,-1,7],[-7,0,7],[-8,0,8],[-9,1,8],[-10,1,9],[-11,2,9],[-11,3,8],[-10,2,8],[-9,2,7],[-8,1,7],[-7,1,6],[-6,0,6],[-5,0,5],[-4,-1,5],[-3,-1,4],[-2,-2,4],[-1,-2,3],[0,-3,3],[1,-3,2],[2,-4,2],[3,-4,1],[4,-5,1],[5,-5,0],[6,-6,0],[7,-6,-1],[8,-7,-1],[9,-7,-2],[10,-8,-2],[11,-8,-3],[11,-7,-4],[10,-7,-3],[9,-6,-3],[8,-6,-2],[7,-5,-2],[6,-5,-1],[5,-4,-1],[4,-4,0],[3,-3,0],[2,-3,1],[1,-2,1],[0,-2,2],[-1,-1,2],[-2,-1,3],[-3,0,3],[-4,0,4],[-5,1,4],[-6,1,5],[-7,2,5],[-8,2,6],[-9,3,6],[-10,3,7],[-11,4,7],[-11,5,6],[-10,4,6],[-9,4,5],[-8,3,5],[-7,3,4],[-6,2,4],[-5,2,3],[-4,1,3],[-3,1,2],[-2,0,2],[-1,0,1],[0,-1,1],[1,-1,0],[2,-2,0],[3,-2,-1],[4,-3,-1],[5,-3,-2],[6,-4,-2],[7,-4,-3],[8,-5,-3],[9,-5,-4],[10,-6,-4],[11,-6,-5],[11,-5,-6],[10,-5,-5],[9,-4,-5],[8,-4,-4],[7,-3,-4],[6,-3,-3],[5,-2,-3],[4,-2,-2],[3,-1,-2],[2,-1,-1],[1,0,-1],[0,0,0],[-1,1,0],[-2,1,1],[-3,2,1],[-4,2,2],[-5,3,2],[-6,3,3],[-7,4,3],[-8,4,4],[-9,5,4],[-10,5,5],[-11,6,5],[-11,7,4],[-10,6,4],[-9,6,3],[-8,5,3],[-7,5,2],[-6,4,2],[-5,4,1],[-4,3,1],[-3,3,0],[-2,2,0],[-1,2,-1],[0,1,-1],[1,1,-2],[2,0,-2],[3,0,-3],[4,-1,-3],[5,-1,-4],[6,-2,-4],[7,-2,-5],[8,-3,-5],[9,-3,-6],[10,-4,-6],[11,-4,-7],[11,-3,-8],[10,-3,-7],[9,-2,-7],[8,-2,-6],[7,-1,-6],[6,-1,-5],[5,0,-5],[4,0,-4],[3,1,-4],[2,1,-3],[1,2,-3],[0,2,-2],[-1,3,-2],[-2,3,-1],[-3,4,-1],[-4,4,0],[-5,5,0],[-6,5,1],[-7,6,1],[-8,6,2],[-9,7,2],[-10,7,3],[-11,8,3],[-11,9,2],[-10,8,2],[-9,8,1],[-8,7,1],[-7,7,0],[-6,6,0],[-5,6,-1],[-4,5,-1],[-3,5,-2],[-2,4,-2],[-1,4,-3],[0,3,-3],[1,3,-4],[2,2,-4],[3,2,-5],[4,1,-5],[5,1,-6],[6,0,-6],[7,0,-7],[8,-1,-7],[9,-1,-8],[10,-2,-8],[11,-2,-9],[11,-1,-10],[10,-1,-9],[9,0,-9],[8,0,-8],[7,1,-8],[6,1,-7],[5,2,-7],[4,2,-6],[3,3,-6],[2,3,-5],[1,4,-5],[0,4,-4],[-1,5,-4],[-2,5,-3],[-3,6,-3],[-4,6,-2],[-5,7,-2],[-6,7,-1],[-7,8,-1],[-8,8,0],[-9,9,0],[-10,9,1],[-11,10,1],[-11,11,0],[-10,10,0],[-9,10,-1],[-8,9,-1],[-7,9,-2],[-6,8,-2],[-5,8,-3],[-4,7,-3],[-3,7,-4],[-2,6,-4],[-1,6,-5],[0,5,-5],[1,5,-6],[2,4,-6],[3,4,-7],[4,3,-7],[5,3,-8],[6,2,-8],[7,2,-9],[8,1,-9],[9,1,-10],[10,0,-10],[11,0,-11],[10,1,-11],[9,2,-11],[8,2,-10],[7,3,-10],[6,3,-9],[5,4,-9],[4,4,-8],[3,5,-8],[2,5,-7],[1,6,-7],[0,6,-6],[-1,7,-6],[-2,7,-5],[-3,8,-5],[-4,8,-4],[-5,9,-4],[-6,9,-3],[-7,10,-3],[-8,10,-2],[-9,11,-2],[-10,11,-1],[-8,11,-3],[-7,11,-4],[-6,10,-4],[-5,10,-5],[-4,9,-5],[-3,9,-6],[-2,8,-6],[-1,8,-7],[0,7,-7],[1,7,-8],[2,6,-8],[3,6,-9],[4,5,-9],[5,5,-10],[6,4,-10],[7,4,-11],[8,3,-11],[6,5,-11],[5,6,-11],[4,6,-10],[3,7,-10],[2,7,-9],[1,8,-9],[0,8,-8],[-1,9,-8],[-2,9,-7],[-3,10,-7],[-4,10,-6],[-5,11,-6],[-6,11,-5],[-4,11,-7],[-3,11,-8],[-2,10,-8],[-1,10,-9],[0,9,-9],[1,9,-10],[2,8,-10],[3,8,-11],[4,7,-11],[2,9,-11],[1,10,-11],[0,10,-10],[-1,11,-10],[-2,11,-9],[0,11,-11]])
adjacency = np.array([[None,1,6,7,8,None],[None,None,2,6,0,None],[None,None,4,5,6,1],[None,None,19,18,17,4],[None,None,3,17,5,2],[2,4,17,16,15,6],[1,2,5,15,7,0],[0,6,15,14,13,8],[None,0,7,13,9,None],[None,8,13,12,11,None],[None,11,32,33,34,None],[None,9,12,32,10,None],[9,13,30,31,32,11],[8,7,14,30,12,9],[7,15,28,29,30,13],[6,5,16,28,14,7],[5,17,26,27,28,15],[4,3,18,26,16,5],[3,19,24,25,26,17],[None,None,20,24,18,3],[None,None,22,23,24,19],[None,None,53,52,51,22],[None,None,21,51,23,20],[20,22,51,50,49,24],[19,20,23,49,25,18],[18,24,49,48,47,26],[17,18,25,47,27,16],[16,26,47,46,45,28],[15,16,27,45,29,14],[14,28,45,44,43,30],[13,14,29,43,31,12],[12,30,43,42,41,32],[11,12,31,41,33,10],[10,32,41,40,39,34],[None,10,33,39,35,None],[None,34,39,38,37,None],[None,37,74,75,76,None],[None,35,38,74,36,None],[35,39,72,73,74,37],[34,33,40,72,38,35],[33,41,70,71,72,39],[32,31,42,70,40,33],[31,43,68,69,70,41],[30,29,44,68,42,31],[29,45,66,67,68,43],[28,27,46,66,44,29],[27,47,64,65,66,45],[26,25,48,64,46,27],[25,49,62,63,64,47],[24,23,50,62,48,25],[23,51,60,61,62,49],[22,21,52,60,50,23],[21,53,58,59,60,51],[None,None,54,58,52,21],[None,None,56,57,58,53],[None,None,None,100,99,56],[None,None,55,99,57,54],[54,56,99,98,97,58],[53,54,57,97,59,52],[52,58,97,96,95,60],[51,52,59,95,61,50],[50,60,95,94,93,62],[49,50,61,93,63,48],[48,62,93,92,91,64],[47,48,63,91,65,46],[46,64,91,90,89,66],[45,46,65,89,67,44],[44,66,89,88,87,68],[43,44,67,87,69,42],[42,68,87,86,85,70],[41,42,69,85,71,40],[40,70,85,84,83,72],[39,40,71,83,73,38],[38,72,83,82,81,74],[37,38,73,81,75,36],[36,74,81,80,79,76],[None,36,75,79,77,None],[None,76,79,78,None,None],[77,79,122,123,None,None],[76,75,80,122,78,77],[75,81,120,121,122,79],[74,73,82,120,80,75],[73,83,118,119,120,81],[72,71,84,118,82,73],[71,85,116,117,118,83],[70,69,86,116,84,71],[69,87,114,115,116,85],[68,67,88,114,86,69],[67,89,112,113,114,87],[66,65,90,112,88,67],[65,91,110,111,112,89],[64,63,92,110,90,65],[63,93,108,109,110,91],[62,61,94,108,92,63],[61,95,106,107,108,93],[60,59,96,106,94,61],[59,97,104,105,106,95],[58,57,98,104,96,59],[57,99,102,103,104,97],[56,55,100,102,98,57],[55,None,None,101,102,99],[100,None,None,146,145,102],[99,100,101,145,103,98],[98,102,145,144,143,104],[97,98,103,143,105,96],[96,104,143,142,141,106],[95,96,105,141,107,94],[94,106,141,140,139,108],[93,94,107,139,109,92],[92,108,139,138,137,110],[91,92,109,137,111,90],[90,110,137,136,135,112],[89,90,111,135,113,88],[88,112,135,134,133,114],[87,88,113,133,115,86],[86,114,133,132,131,116],[85,86,115,131,117,84],[84,116,131,130,129,118],[83,84,117,129,119,82],[82,118,129,128,127,120],[81,82,119,127,121,80],[80,120,127,126,125,122],[79,80,121,125,123,78],[78,122,125,124,None,None],[123,125,168,169,None,None],[122,121,126,168,124,123],[121,127,166,167,168,125],[120,119,128,166,126,121],[119,129,164,165,166,127],[118,117,130,164,128,119],[117,131,162,163,164,129],[116,115,132,162,130,117],[115,133,160,161,162,131],[114,113,134,160,132,115],[113,135,158,159,160,133],[112,111,136,158,134,113],[111,137,156,157,158,135],[110,109,138,156,136,111],[109,139,154,155,156,137],[108,107,140,154,138,109],[107,141,152,153,154,139],[106,105,142,152,140,107],[105,143,150,151,152,141],[104,103,144,150,142,105],[103,145,148,149,150,143],[102,101,146,148,144,103],[101,None,None,147,148,145],[146,None,None,192,191,148],[145,146,147,191,149,144],[144,148,191,190,189,150],[143,144,149,189,151,142],[142,150,189,188,187,152],[141,142,151,187,153,140],[140,152,187,186,185,154],[139,140,153,185,155,138],[138,154,185,184,183,156],[137,138,155,183,157,136],[136,156,183,182,181,158],[135,136,157,181,159,134],[134,158,181,180,179,160],[133,134,159,179,161,132],[132,160,179,178,177,162],[131,132,161,177,163,130],[130,162,177,176,175,164],[129,130,163,175,165,128],[128,164,175,174,173,166],[127,128,165,173,167,126],[126,166,173,172,171,168],[125,126,167,171,169,124],[124,168,171,170,None,None],[169,171,214,215,None,None],[168,167,172,214,170,169],[167,173,212,213,214,171],[166,165,174,212,172,167],[165,175,210,211,212,173],[164,163,176,210,174,165],[163,177,208,209,210,175],[162,161,178,208,176,163],[161,179,206,207,208,177],[160,159,180,206,178,161],[159,181,204,205,206,179],[158,157,182,204,180,159],[157,183,202,203,204,181],[156,155,184,202,182,157],[155,185,200,201,202,183],[154,153,186,200,184,155],[153,187,198,199,200,185],[152,151,188,198,186,153],[151,189,196,197,198,187],[150,149,190,196,188,151],[149,191,194,195,196,189],[148,147,192,194,190,149],[147,None,None,193,194,191],[192,None,None,238,237,194],[191,192,193,237,195,190],[190,194,237,236,235,196],[189,190,195,235,197,188],[188,196,235,234,233,198],[187,188,197,233,199,186],[186,198,233,232,231,200],[185,186,199,231,201,184],[184,200,231,230,229,202],[183,184,201,229,203,182],[182,202,229,228,227,204],[181,182,203,227,205,180],[180,204,227,226,225,206],[179,180,205,225,207,178],[178,206,225,224,223,208],[177,178,207,223,209,176],[176,208,223,222,221,210],[175,176,209,221,211,174],[174,210,221,220,219,212],[173,174,211,219,213,172],[172,212,219,218,217,214],[171,172,213,217,215,170],[170,214,217,216,None,None],[215,217,260,261,None,None],[214,213,218,260,216,215],[213,219,258,259,260,217],[212,211,220,258,218,213],[211,221,256,257,258,219],[210,209,222,256,220,211],[209,223,254,255,256,221],[208,207,224,254,222,209],[207,225,252,253,254,223],[206,205,226,252,224,207],[205,227,250,251,252,225],[204,203,228,250,226,205],[203,229,248,249,250,227],[202,201,230,248,228,203],[201,231,246,247,248,229],[200,199,232,246,230,201],[199,233,244,245,246,231],[198,197,234,244,232,199],[197,235,242,243,244,233],[196,195,236,242,234,197],[195,237,240,241,242,235],[194,193,238,240,236,195],[193,None,None,239,240,237],[238,None,None,284,283,240],[237,238,239,283,241,236],[236,240,283,282,281,242],[235,236,241,281,243,234],[234,242,281,280,279,244],[233,234,243,279,245,232],[232,244,279,278,277,246],[231,232,245,277,247,230],[230,246,277,276,275,248],[229,230,247,275,249,228],[228,248,275,274,273,250],[227,228,249,273,251,226],[226,250,273,272,271,252],[225,226,251,271,253,224],[224,252,271,270,269,254],[223,224,253,269,255,222],[222,254,269,268,267,256],[221,222,255,267,257,220],[220,256,267,266,265,258],[219,220,257,265,259,218],[218,258,265,264,263,260],[217,218,259,263,261,216],[216,260,263,262,None,None],[261,263,306,307,None,None],[260,259,264,306,262,261],[259,265,304,305,306,263],[258,257,266,304,264,259],[257,267,302,303,304,265],[256,255,268,302,266,257],[255,269,300,301,302,267],[254,253,270,300,268,255],[253,271,298,299,300,269],[252,251,272,298,270,253],[251,273,296,297,298,271],[250,249,274,296,272,251],[249,275,294,295,296,273],[248,247,276,294,274,249],[247,277,292,293,294,275],[246,245,278,292,276,247],[245,279,290,291,292,277],[244,243,280,290,278,245],[243,281,288,289,290,279],[242,241,282,288,280,243],[241,283,286,287,288,281],[240,239,284,286,282,241],[239,None,None,285,286,283],[284,None,None,330,329,286],[283,284,285,329,287,282],[282,286,329,328,327,288],[281,282,287,327,289,280],[280,288,327,326,325,290],[279,280,289,325,291,278],[278,290,325,324,323,292],[277,278,291,323,293,276],[276,292,323,322,321,294],[275,276,293,321,295,274],[274,294,321,320,319,296],[273,274,295,319,297,272],[272,296,319,318,317,298],[271,272,297,317,299,270],[270,298,317,316,315,300],[269,270,299,315,301,268],[268,300,315,314,313,302],[267,268,301,313,303,266],[266,302,313,312,311,304],[265,266,303,311,305,264],[264,304,311,310,309,306],[263,264,305,309,307,262],[262,306,309,308,None,None],[307,309,351,None,None,None],[306,305,310,351,308,307],[305,311,349,350,351,309],[304,303,312,349,310,305],[303,313,347,348,349,311],[302,301,314,347,312,303],[301,315,345,346,347,313],[300,299,316,345,314,301],[299,317,343,344,345,315],[298,297,318,343,316,299],[297,319,341,342,343,317],[296,295,320,341,318,297],[295,321,339,340,341,319],[294,293,322,339,320,295],[293,323,337,338,339,321],[292,291,324,337,322,293],[291,325,335,336,337,323],[290,289,326,335,324,291],[289,327,333,334,335,325],[288,287,328,333,326,289],[287,329,331,332,333,327],[286,285,330,331,328,287],[285,None,None,None,331,329],[329,330,None,None,332,328],[328,331,None,None,368,333],[327,328,332,368,334,326],[326,333,368,367,366,335],[325,326,334,366,336,324],[324,335,366,365,364,337],[323,324,336,364,338,322],[322,337,364,363,362,339],[321,322,338,362,340,320],[320,339,362,361,360,341],[319,320,340,360,342,318],[318,341,360,359,358,343],[317,318,342,358,344,316],[316,343,358,357,356,345],[315,316,344,356,346,314],[314,345,356,355,354,347],[313,314,346,354,348,312],[312,347,354,353,352,349],[311,312,348,352,350,310],[310,349,352,None,None,351],[309,310,350,None,None,308],[349,348,353,None,None,350],[348,354,381,None,None,352],[347,346,355,381,353,348],[346,356,379,380,381,354],[345,344,357,379,355,346],[344,358,377,378,379,356],[343,342,359,377,357,344],[342,360,375,376,377,358],[341,340,361,375,359,342],[340,362,373,374,375,360],[339,338,363,373,361,340],[338,364,371,372,373,362],[337,336,365,371,363,338],[336,366,369,370,371,364],[335,334,367,369,365,336],[334,368,None,None,369,366],[333,332,None,None,367,334],[366,367,None,None,370,365],[365,369,None,None,390,371],[364,365,370,390,372,363],[363,371,390,389,388,373],[362,363,372,388,374,361],[361,373,388,387,386,375],[360,361,374,386,376,359],[359,375,386,385,384,377],[358,359,376,384,378,357],[357,377,384,383,382,379],[356,357,378,382,380,355],[355,379,382,None,None,381],[354,355,380,None,None,353],[379,378,383,None,None,380],[378,384,395,None,None,382],[377,376,385,395,383,378],[376,386,393,394,395,384],[375,374,387,393,385,376],[374,388,391,392,393,386],[373,372,389,391,387,374],[372,390,None,None,391,388],[371,370,None,None,389,372],[388,389,None,None,392,387],[387,391,None,None,396,393],[386,387,392,396,394,385],[385,393,396,None,None,395],[384,385,394,None,None,383],[393,392,None,None,None,394]])
  
g = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
      1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2,
      2, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5,
      5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10,
      10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
      17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
      25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
      37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
      51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
      69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
      90, 92, 93, 95, 96, 98, 99,101,102,104,105,107,109,110,112,114,
      115,117,119,120,122,124,126,127,129,131,133,135,137,138,140,142,
      144,146,148,150,152,154,156,158,160,162,164,167,169,171,173,175,
      177,180,182,184,186,189,191,193,196,198,200,203,205,208,210,213,
      215,218,220,223,225,228,231,233,236,239,241,244,247,249,252,255 ]

orangblue_p = [[0,0,0],
		[99,	227,	232],
		[124,	204,	232],
		[150,	181,	232],
		[175,	158,	232],
		[201,	135,	232],
		[255,	164,	70],
		[250,	135,	97],
		[245,	105,	124],
		[240,	76,	151],
		[235,	46,	178],
		[230,	15,	200]]

sunset_palette_r = [[0,0,0],
		[255, 255, 240],
		[255,	233,	192],
		[255,	211,	128],
		[255,	166,	0],
		[255,	133,	49],
		[255,	99,	97],
		[188,	80,	144],
		[138,	80,	143],
		[44,	72,	117],
		[0,	63,	92],
		[0,	32,	46]]

sunset_palette = [[0,0,0],
		[0,	32,	46],
		[0,	63,	92],
		[44,	72,	117],
		[138,	80,	143],
		[188,	80,	144],
		[255,	99,	97],
		[255,	133,	49],
		[255,	166,	0],
		[255,	211,	128],
		[255,	233,	192],
		[255, 255, 240]]

rainbow_p = [[0,0,0],
		[255, 0, 0],
                [200, 50, 0],
                [150, 100, 0],
                [100, 150, 0],
                [50, 200, 0], #5
                [0, 255, 50],
                [0, 200, 100],
                [0, 150, 150],
                [0, 100, 200],
                [0, 50, 250], #10
                [50, 0, 250]]

patina_p = [[0,0,0],
[42,	101,	119],
[50,	104,	110],
[57,	106,	100],
[87,	101,	129],
[132,	132,	101],
[140,	132,	99],
[112,	104,	81],
[108,	81,	59],
[100,	78,	60],
[89,	54,	39],
[76,	29,	18]]

hazy_p = [[0,0,0],
[138,	235,	169],
[130,	192,	159],
[122,	148,	148],
[139,	136,	149],
[155,	123,	150],
[188,	125,	138],
[222,	136,	145],
[255,	147,	151],
[255,	154,	128],
[255,	167,	128],
[255,   190,    110]]


earthy_p = [[0,0,0],
[247,	235,	216],
[243,	227,	201],
[239,	219,	187],
[235,	211,	173],
[230,	203,	159],
[225,	194,	146],
[220,	186,	133],
[203,	156,	125],
[186,	130,	116],
[169,	107,	108],
[152,	98,	111]]
