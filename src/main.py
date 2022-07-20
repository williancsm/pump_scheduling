import sys
import numpy as np

sys.path.append('include')

WORK_STEP = 24
SCHEDULE_FILE = "data/schedule.txt"
NETWORK_FILE = "data/vanZyl.inp"

import epanet_module as em

def HydrantRating( MyNode, Demands):
   #Open the EPANET toolkit & hydraulics solver
   em.ENopen( "data/example2.inp", "example2.rpt" )
   em.ENopenH()

   # Get the index of the node of interest
   nodeindex= em.ENgetnodeindex(MyNode);

   rating= []
   # Iterate over all demands
   for dem in Demands:
      em.ENsetnodevalue(nodeindex, em.EN_BASEDEMAND, dem)
      em.ENinitH(em.EN_NOSAVE)
      em.ENrunH()
      pressure= em.ENgetnodevalue(nodeindex, em.EN_PRESSURE)
      rating.append(pressure)

   # Close hydraulics solver & toolkit */
   em.ENcloseH()
   em.ENclose()
   return rating


if __name__=='__main__':
	inp_filename = "data/vanZyl.inp"
	em.ENopen( inp_filename, "output.rpt" )
	
	num_links       = em.ENgetcount( em.EN_LINKCOUNT )
	num_juncs       = em.ENgetcount( em.EN_JUNCSCOUNT )
	num_pumps       = em.ENgetcount( em.EN_PUMPCOUNT )
	num_tanks       = em.ENgetcount( em.EN_TANKCOUNT )
	num_reservoirs  = em.ENgetcount( em.EN_RESERVCOUNT )
	num_tanks       = num_tanks - num_reservoirs
	
	print( "Network: {0}: {1} links  {2} junctions  {3} pumps and  {4} tanks\n\n".format( inp_filename, num_links, num_juncs, num_pumps, num_tanks ) )

	pump_index = np.zeros( num_pumps, dtype = int )
	pump_id    = np.ndarray( shape = (num_pumps, ), dtype = object )
	for i in range( num_pumps ):
		pump_index[ i ] = em.ENgetpumpindex( i + 1 )
		pump_id[ i ]    = em.ENgetlinkid( int( pump_index[ i ] ) ).decode( "utf-8" )

	tank_index = np.zeros( num_tanks, dtype = int )
	tank_id    = np.ndarray( shape = ( num_tanks, ), dtype = object )
	for i in range( num_tanks ):
		tank_index[ i ] = em.ENgettankindex( i + 1 )
		tank_id[ i ]    = em.ENgetnodeid( int( tank_index[ i ] ) ).decode( "utf-8" )

	pattern_index = np.zeros( num_pumps, dtype = int )
	for i in range( num_pumps ):
		em.ENaddpattern( pump_id[ i ] )
		pattern_index[ i ] = em.ENgetpatternindex( pump_id[ i ] )

	patterns = np.zeros( ( num_pumps, WORK_STEP ), dtype = int )
	with open( SCHEDULE_FILE, "r" ) as fp:
		for count, line in enumerate( fp ):
			if count > ( num_pumps - 1 ):
				print( "Number of patterns GREATER than the number of pumps!")
				print( "Using the first {}.".format( num_pumps ) )
			else:
				for step, pr in enumerate( line.strip( '\n' ) ):
					if step < WORK_STEP:
						patterns[ count ][ step ] = int( pr )
					else:
						print( "Numer of steps (hours) GREATER than {}".format( WORK_STEP ))
		if count < (num_pumps - 1 ):
			print( "Number of patterns LESS than the number of pumps!")
			exit( -1 )


	for p in range( num_pumps ):
		em.ENsetpattern( pattern_index[ p ], patterns[ p ] )
		pump_index[ p ] = em.ENgetlinkindex( pump_id[ p ] )
		em.ENsetlinkvalue( pump_index[p], em.EN_UPATTERN, pattern_index[p] )

	em.ENsolveH()

	print( "Pump: (Switches)[MinIdleTime]: Schedule" )

	total_sw = 0
	min_idletime = float( "inf" )
	for i in range( num_pumps ):
		sw = em.ENgetpumpswitches( int( pump_index[ i ] ) )
		print( "{}: ({:8d})".format( pump_id[ i ], sw ), end = '' )
		total_sw += sw

		idletime = em.ENgetminstoptime( int( pump_index[i] ) )
		print( "[{:11d}]: ".format( idletime ), end = '' )
		
		if idletime > 0:
			min_idletime = min(min_idletime, idletime);

		for step in range( WORK_STEP ):
			value = em.ENgetpatternvalue( int( pattern_index[i] ), step + 1 )
			print( "{:.0f}".format( value ), end = '' )
		print( )

	print( "-------------------------------------------------------------" )
	print( "Total switches = {}, Min Idle Time = {} ".format( total_sw, min_idletime ) )
	print( )
	print( " Tank: Head(0) - Head = dHead : V(0) - Volume = dVolume" )

	totaltanks = 0
	for i in range( num_tanks ):
		tanklevel = em.ENgetnodevalue ( int( tank_index[i] ), em.EN_TANKLEVEL )
		elevation = em.ENgetnodevalue ( int( tank_index[i] ), em.EN_ELEVATION )
		head      = em.ENgetnodevalue ( int( tank_index[i] ), em.EN_HEAD )
		initvol   = em.ENgetnodevalue ( int( tank_index[i] ), em.EN_INITVOL )
		volume    = em.ENgetnodevalue ( int( tank_index[i] ), em.EN_VOLUME )
		
		print( "{}: {:4.2f} - {:4.2f} = {:+.2f} "
					        ": {:7.2f} - {:7.2f} = {:+6.2f} ".format( tank_id[i],  tanklevel + elevation, head, tanklevel + elevation - head, initvol, volume, initvol - volume ) )
		
		totaltanks += initvol - volume

	print( )
	
	demand = em.ENgettotaldemand( ) 
	
	print ( "Total demand: {:10.2f} ".format( demand ) )
	
	inflow = em.ENgettotalinflow( )
	
	print ("Total inflow: {:10.2f} ".format( inflow ) )
	print ("             = {:10.4f} ".format( demand + inflow ) )
	print ( "Total tanks:  {:10.4f} m^3 ".format( totaltanks ) )
	print (" Difference = {:.2f} ".format( totaltanks * 1.0e+03 - ( demand  + inflow ) ) )
				 
	inflow = em.ENgettotalleakage( )
	
	print( "Total leakage: {:.2f} ".format( inflow ) )
	print( )
	
	totalcost = em.ENgettotalenergycost( )
	print( "Total energy cost:   {:10.2f} ".format( totalcost ) )

	em.ENclose()