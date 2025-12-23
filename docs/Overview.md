Relay Logic Simulator

We are going to build a relay logic simulator. This will initally have 4 types of components. A Toggle Switch, an Indicator (LED), a DPDT Relay, and VCC (power source).

We are first of all going to concentrate on the Simulation Engine, then we can build the front end later.

I want to control the simulator via a telnet type terminal. All debugging will also be via the terminal. The terminal will be enabled by default for now. I want to use standard Terminal / Telnet software.

You will interact with the engine via the terminal interface.

The simulation engine has both **single-threaded** and **multi-threaded** modes. Based on comprehensive performance analysis:
- **Single-threaded** (default) is 2x faster for circuits <2000 components
- **Multi-threaded** is beneficial for circuits ≥2000 components
- **AUTO mode** automatically selects optimal engine based on component count

VNET processing and Component processing are parallelized in multi-threaded mode using a thread pool model. However, performance profiling revealed threading overhead exceeds benefits for typical circuit sizes. See `THREADING_BOTTLENECK_ANALYSIS.md` for details.

Eventually there will be a front end application where I can design schematics, watch the simulated responses and interact with components.

# Simulation Engine overview.

## Element ID's

* A Simulation document will have a .rsim file extension and contain multiple pages. 

* Every new page will have a unique ID called pageID. 
  This will be the first 8 characters of a UUID. This will be standard even if a Documnent only has a single page.

* All ID's used in the application will be shortenend to the first 8 characters.

* Every component, wire junction and waypoint and Pin etc. placed in a drawing will be assigned it's own unique UUID.

* These ID's will be hierarchical in nature: Examples are:

    PageId.ComponentId.PinId
    PageId.ComponentId.PinId.TabId
    PageId.WireId.waypointId
    PageId.WireId.JunctionId

    These will be stored hierarchically in the .rsim file


## COMPONENT HIERARCHY

    PageId
        ComponentId
            PinId
            PinId
        ComponentId
            PinId
        WireId
            TabId
            waypointId
            waypointId
            JunctionId
                waypointId
                TabId
            TabId
    etc.

* Whenever we COPY and paste objects a completely new ID's will be generated for the new objects including the current pageID.
  If we CUT and paste on the same page the ID's will be retained.
  If we CUT and paste to a different page the Id's will be maintained EXCEPT for the pageID which will be replaced.

NO OBJECT SHOULD HAVE A DUPLICATE ID.

## Pins and Tabs

* A COMPONENT can have many PINS and a PIN can have multiple TABS. For example an Indicator will have one PIN but 4 TABS.  Each tab will have it's 
  own position on the component. For Example a Indicator will have 4 TABS at 3,6,9 and 12 o'clock positions, all connected to the same PIN.
  The state of the indicator (HIGH or FLOAT) will be read from the state of the PIN not the TABS.

* Electrically the TABS will refelect the status of the PIN. 4 different wires could be connected to the 4 different TABS of the same PIN.
  If any TAB goes HIGH they all go HIGH, and this state is passed to the PIN. Conversely if the PIN goes HIGH the TABS would also GO HIGH.

  A pin is a collection of TABS, even if it only has one TAB.

## Components
* Components will have a Position and other properties specific to it.
 
* When adding a new component to a canvas default values should be applied.

* When Copying a component all properties should be copied too.

* Components should be kept in their own Class files. NO component specific code should be in the main application.

* A component class needs to have a three Key routines

    1) The Component Logic - This is what the Engine will use to re-calculate the components status. 
       This logic will read the STATE of all the components PINS, calculate the NEW STATE of its pins, then if required will make the VNET connected to
       one of it's pins 'Dirty' if required.

    2) Update code - This will redraw the component in the designer based on the state of it's internal PIN states. This only needs to be run if the
       component is on the same page as we are viewing.
    
    3) Interaction Code - The interaction code will also handle any user interaction with the component and adjust the PIN states accordingly.
       Interaction might be from pressing the button on the canvas or it might come from a different source (an api for example that allows a button
       to be pressed remotely).
    
    4) Sim Start - This is when the Simulation Starts. This sets defaults for the component and sets up BRIDGES (see below) etc.

    5) Sim Stop - This is when the Simulation Starts. This will be used to clear down internal states of the component if required.


## WIRES AND JUNCTIONS

* All and Pins are bidirectional

* WIRES are connections drawn between component TABS.

* WIRES can have JUNCTIONS on them to connect multiple components. If I connect two wires using a junction electrically they wil all be connected.

* WIRES have waypoints, where we can change the directions of the wire while designing. They have no effect on the electical connection.

    Here is the structure of a WireId:
    
    WireId
        TabId - Component_A
        waypointId
        waypointId
            JunctionId
                WireId
                    waypointId
                    TabId - Component_B
                WireId
                    waypointId
                    TabId - Component_C
        TabId


In the above example you have a wire starting at one TAB, being routed with two waypoints then we have a junction. Two other wires are connected to this
junction with their own wires. This makes deleting a wire or adding a junction fairly straight forward.

## VNETS

Consider the wiring example above this would be converted into a VNET (Virtual Network) when the simulator starts. The VNET simplifies processing by 
discarding unnecessary information. The VNET only contains the TABS that are electicaly connected:

VnetId
    TabId - Component_A
    TabId - Component_B
    TabId - Component_C

## Links
* When we start building VNETS (Virtual Nets) we will only build VNETS that are on the same page. VNETS will not be created across pages. 
  The VNET builder will use the pageID part of the identifier to determine what to merge and what it can't.

* Links are connections that can be used to connect VNET's together by a NAME rather than a wire. 
  LINKS can be on the same or DIFFERENT Pages, they act like a virtual wire.

* LINKS will analysed by looking at components Components can have a property of 'Link Name'.
  The components will have the pageID.componentID format.

  The VNET would then look like this:
  
  VnetId
    TabId - Component_A
    TabId - Component_B
    TabId - Component_C
    Link("TestLink")
    
## VNET Processing.

* In this simulator we do not use HIGH and LOW. we use HIGH and FLOAT. HIGH will always override a FLOAT.
    Example: If we have two TABS connected together by a wire.
            TAB_A = FLOAT and TAB_B = FLOAT then the VNET is FLOAT
            TAB_A = HIGH and TAB_B = FLOAT THE VNET is HIGH AND TAB_B will also be driven HIGH.
            TAB_A = FLOAT and TAB_B = HIGH THE VNET is HIGH AND TAB_A will also be driven HIGH.
            TAB_A = HIGH and TAB_B = HIGH THE VNET is HIGH.

    This is based arount a logical OR type logic. If one is high ALL are HIGH.

* If a component changes the state of one of it's pins so that is different to the current state of the VNET it will set a flag 
  on that pins VNET marking the VNET 'Dirty'.

* If a LINK connected to a VNET changes state so that is different to the current state of the VNET it will set a flag 
  on that pins VNET marking the VNET 'Dirty'.

* When the simulation is running, the VNET engine will look at each VNET. If the VNET is dirty it will trigger all components
to update their logic and move on to the next VNET. Leaving the components to process async of the VNET engine using the thread pools.

* Looping through all the VNETS and evaluating them will be constant while the simulation is running. 
  The processing of only processing 'Dirty' VNETs means unchanged stable VNETS can be ignored which will improve performance.

* The simulation will be considered stable when there are no 'dirty' VNETS left to process. At this point the stable state 
  will be available to the Front End to redraw.

* The front end will not redraw while the engine is processing 'Dirty' VNETS and is unstable.

## Modifying VNET's

* Component logic must be able to connect and disconnet VNETS together. For example, a relay component has a COM, NO and NC polls.
  We will create a special LINK case called a BRIDGE (a component bridge) for every relay dynamically on simulation start.

  Consider I have a relay with a COM, NC and NO pins. When the relay is not energised the COM and NC of the relay must be
  connected together. We will add a special type of link called a BRIDGE to the COM pin's VNET Connecting it to the NC's PIN VNET.

  This will be built by the components sim start code at runtime, and is rebuilt at every Sim start. This is not saved to the .rsim file.

  In the example below the BRIDGE (like a link) as connected COM to NC.

  COM.Vnet -- VNET on the COM pin of the relay.
    TabId - Component_A
    TabId - Component_B
    TabId - Component_C
    BRIDGE bridgeId -- The bridgeId is allocated at runtime and added to the COM vnet by the component instance sim start routine.

  NC.Vnet
    TabId - Component_D
    TabId - Component_E
    TabId - Component_F
    BRIDGE bridgeId 

  NO.Vnet
    TabId - Component_G
    TabId - Component_H
    TabId - Component_I

  If the coil is energised and the contacts switch, the BRIDGE will be removed from the NC.Vnet and added to the NO.Vnet.

  NC.Vnet
    TabId - Component_D
    TabId - Component_E
    TabId - Component_F

  NO.Vnet
    TabId - Component_G
    TabId - Component_H
    TabId - Component_I
    BRIDGE bridgeId 

    Then the vnets will be marked 'Dirty' to be recalculated.



