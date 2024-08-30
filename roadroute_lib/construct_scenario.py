import numpy as np

nm  = 1852.                 # m    of 1 nautical mile

sharpturn_lim = 35.
turn_lim = 25.

def kwikqdrdist(lata, lona, latb, lonb):
    """Gives quick and dirty qdr[deg] and dist [nm]
       from lat/lon. (note: does not work well close to poles)"""

    re      = 6371000.  # radius earth [m]
    dlat    = np.radians(latb - lata)
    dlon    = np.radians(((lonb - lona)+180)%360-180)
    cavelat = np.cos(np.radians(lata + latb) * 0.5)

    dangle  = np.sqrt(dlat * dlat + dlon * dlon * cavelat * cavelat)
    dist    = re * dangle / nm

    qdr     = np.degrees(np.arctan2(dlon * cavelat, dlat)) % 360.

    return qdr, dist

def construct_scenario(truckname, road_route, spd_lims, turn_spd=10, 
                sharpturn_spd=5, sharpturn_lim=sharpturn_lim,   
                turn_lim=turn_lim, cruise_alt=0):
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