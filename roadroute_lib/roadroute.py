from shapely.geometry import LineString
import taxicab_st as ts
from osmnx.routing import route_to_gdf

def reverse_linestring(ls):
    return LineString(ls.coords[::-1])

def construct_scenario(truckname, road_route, spd_lims, turn_spd=10, 
                sharpturn_spd=5, sharpturn_lim=35, turn_lim=25, cruise_alt=0):
    """Construct the scenario text for the waypoints of the road route.
    
    Args:
        - truckname: string, name of the truck that needs to be routed
        - road_route: LineString, the road route as a LineString
        - spd_lims: list, speed limits of the road route's LineStrings
        - turnspd: float/ int, turning speed in kts
        - sharpturn_spd: float/ int, turning speeds for sharp corners in kts
        - sharpturn_lim: float/ int, threshold limit for sharp turns in deg
        - turn_lim: float/ int, threshold limit for turns in deg
        - cruise_alt: float/ int, cruise altitude in ft
    """
    route_waypoints = list(zip(road_route.xy[1], road_route.xy[0]))
    route_lats = road_route.xy[1]
    route_lons = road_route.xy[0]
    i = 1 # Start at second waypoint
    # Doesn't matter what the first waypoint is designated as, 
    # so just have it as true.
    turns = ['turn'] 
    for lat_cur, lon_cur in route_waypoints[1:-1]:
        # Get the previous and the next waypoint
        lat_prev, lon_prev = route_waypoints[i-1]
        lat_next, lon_next = route_waypoints[i+1]
        # Get the angle
        a1, _ = kwikqdrdist(lat_prev,lon_prev,lat_cur,lon_cur)
        a2, _ = kwikqdrdist(lat_cur,lon_cur,lat_next,lon_next)
        angle=abs(a2-a1)
        if angle>180:
            angle=360-angle
        # In general, we noticed that we don't need to slow down if 
        # the turn is smaller than 25 degrees
        # If the angle is larger, then a more severe slowdown is required
        #  However, this will depend on the cruise speed of the vehicle.
        if angle > sharpturn_lim:
            turns.append('sharpturn')
        elif angle > turn_lim:
            turns.append('turn')
        else:
            turns.append('straight')
        i += 1

    # Let the vehicle slow down for the depot
    turns.append(True)
    scen_text = ""

    # We can do that using the ADDTDWAYPOINTS command.
    # ADDTDWAYPOINTS can chain waypoint data in the following way:
    # ADDTDWAYPOINTS ACID LAT LON ALT SPD Turn? TurnSpeed
    # Initiate addtdwaypoints command
    scen_text += f'ADDTDWAYPOINTS {truckname}'
    # Loop through waypoints
    for wplat, wplon, turn, spdlim in zip(route_lats, route_lons, turns, 
                                                                spd_lims):
        # Check if this waypoint is a turn
        if turn == 'turn' or turn == 'sharpturn':
            wptype = 'TURNSPD'
            wp_turnspd = turn_spd if turn == 'turn' else sharpturn_spd
        else:
            wptype = 'FLYBY'
            # Doesn't matter what we pick here, as long as it is assigned. 
            # Will be ignored
            wp_turnspd = turn_spd
        # Add the text for this waypoint. 
        # It doesn't matter if we always add a turn speed, as BlueSky will
        # ignore it if the wptype is set as FLYBY
        cruisespd = spdlim
        scen_text += f',{wplat},{wplon},{cruise_alt},{cruisespd},{wptype},{wp_turnspd}'

    return scen_text

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

# A = np.array([42.876466914460224, -78.78590820757644])
# B = np.array([42.868358900000004, -78.8312416])
# # A = (G.nodes[7779745399]['y'], G.nodes[7779745399]['x'])
# # B = (G.nodes[11209177619]['y'], G.nodes[11209177619]['x'])
# A = np.array([42.88189546413181, -78.74404160878684])
# B = np.array([42.88198599999998, -78.746419])

# q,w,e= roadroute(G,A,B)   

# print(len(e), len(linemerge(q).coords))