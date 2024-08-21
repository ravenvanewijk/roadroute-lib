from shapely.geometry import LineString
import taxicab_st as ts
from osmnx.routing import route_to_gdf

def reverse_linestring(ls):
    return LineString(ls.coords[::-1])

def roadroute(G, A, B, speed_attr='maxspeed_kts', def_spd=26.07):
    """Compute the road route from point A to point B using the taxicab distance.
    
    Args:
        - A: tuple/ list of floats, the starting point (lat, lon)
        - B: tuple/ list of floats, the destination point (lat, lon)
    """
    route = []
    spdlims = []
    routepart = ts.time.shortest_path(G, [A[0], A[1]], 
                                                [B[0], B[1]])

    if type(routepart[2]) != list:
        # routepart at beginning
        route.append(routepart[2])
        # First time you have to get 2 speed limits, first wp spdlim does not 
        # matter, will be reached instantly
        spdlims.extend([def_spd] * (len(routepart[2].coords)))
    
    else:
        # We dont have a beginning so we can just add the default speed to the
        # beginning
        spdlims.extend([def_spd])

    try:
        gdf = route_to_gdf(G,routepart[1])
        # For every pair of edges, append the route with the 
        # Shapely LineStrings
        for idx, row in gdf.iterrows():
            if 'geometry' in row:
                # Some edges have this attribute embedded
                route.append(row['geometry'])
                spdlims.extend([row[speed_attr]] * \
                    (len(row['geometry'].coords) - 1))
                # Other edges don't have this attribute. 
                # These are straight lines between their two nodes.
            else:
                # So, get a straight line between the nodes 
                # and append that line piece
                route.append(LineString([(G.nodes[u]['x'], G.nodes[u]['y']), 
                        (G.nodes[v]['x'], G.nodes[v]['y'])]))
                spdlims.extend([row[speed_attr]])

    except ValueError:
        # No edges in routepart[1], continue with route
        pass
    
    try:
        # Additional check for first linepart directionality. Sometimes it might be facing the wrong way.
        # The end of the beginning (incomplete) linestring should match
        try:
            if not route[1].coords[0] == routepart[2].coords[-1]:
                # Check if flipped version does align
                if route[1].coords[0] == routepart[2].coords[0]:
                    route[0] = reverse_linestring(route[0])
                else:
                    raise Exception('Taxicab alignment Error: Coordinates of beginning LineString does not align')
        except IndexError:
            pass
    except AttributeError:
        pass

    try:
        # Check whether final incomplete linestring is in proper direction, similar check
        try:
            if not route[-1].coords[-1] == routepart[3].coords[0]:
                # Check if flipped version does align
                if route[-1].coords[-1] == routepart[3].coords[-1]:
                    route.append(reverse_linestring(routepart[3]))

                # Rare exception where the first linepiece was added in 
                # the wrong direction. Only occurs where routepart[1] == []
                elif route[-1].coords[0] == routepart[3].coords[0]:
                    route[0] = reverse_linestring(route[0])
                    route.append(routepart[3])
                elif route[-1].coords[0] == routepart[3].coords[1]:
                    route[0] = reverse_linestring(route[0])
                    route.append(reverse_linestring(routepart[3]))
                else:
                    raise Exception('Taxicab alignment Error: Coordinates of final LineString does not align')
            else:
                route.append(routepart[3])
            spdlims.extend([def_spd] * (len(routepart[3].coords) - 1))
        except IndexError:
            pass
    except AttributeError or IndexError:
        pass
    return route, spdlims, routepart[4]


# import osmnx as ox
# import numpy as np
# import matplotlib.pyplot as plt
# import pandas as pd
# from shapely import Point
# from shapely.ops import linemerge



# def str_interpret(value):
#     return value  # Ensure the value remains a string

# G = ox.load_graphml(filepath='roadroute_lib/Buffalo.graphml',
#                         edge_dtypes={'osmid': str_interpret,
#                                     'reversed': str_interpret})



# # A = np.array([ 42.872692, -78.881017])
# # B = np.array([ 42.852731, -78.815075])
# A = (42.87571, -78.731316)

# B = np.array([ 42.920952, -78.744525])

# q,w,e= roadroute(G,A,B)   

# print(len(e), len(linemerge(q).coords))