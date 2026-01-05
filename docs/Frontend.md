We want to create a modern UI for the logic simulator.

We will use tkinter but with a modern Dark theme.
I want this to be styled to match a Visual Studio Code / Modern IDE feel.

The app will save persistant settings not in the .rsim file. These include (for now).
    Recent Documents
    Simulation Threading settings (set as single thread by default)
    Default Canvas Size (set at 3000x3000 by default)

The designer will run in two modes:

    Design mode
        Full editing allowed. User and add components, wires and junctions etc.
        Copy and paste enabled
        Component Toolbar visible.
        User can adjust properties but not interact with simulation (Cannot toggle a switch)

    Simulation mode

        No editing of the drawing will be allowed while the simulation is running. 
        While running the simulation the component toolbar will be hidden.
        Loading and saving schematics disabled.
        Copy and Paste Disabled.

Window Elements

    Top Toolbar
        Buttons for Start / Stop Simulation and Pause SIM.

    Components Toolbar
        There will be a components toolbar that will dynamically load components on the left hand side of the window.

    Properties Window
        A properties toolbar will be on the right hand side.
        The toolbar will have a moden visual studio style layout wich peropertes grouped in sections.

    Canvas
        The the total canvas area on each page will be 3000x3000px.
        The canvas will have a grid of 20px with a grid snap of 10px.
        We will be able to zoom in and out of the canvas.
        The canvas will have horizontal and vertical scroll bars.
        Right hand click and drag to pan

    Bottom Status bar
        The satus bar will have the current zoom level

    Page selection bar
        Page selection bar will be positioned just above the canvas area. 
        Pages will look like tabs.
        Pages shoud be able to be renamed and re-ordered and deleted.

    File selection bar
        The file selection bar will sit above the page selection bar.
        WE will be able to open multiple files.
        When we switch documents it will wipe and force a complete reload of the document.
        We can ony switch documents when the simulator is stopped.
        We we will need a recent items file

Menu 
    File
        New
        Open
        Save
        Save As
        Settings
        Exit
    Edit
        Select All
        Cut
        Copy
        Paste
    Simulation
        Simulation Start
        Simulation Stop
    View
        Zoom in 
        Zoom out
        Reset zoom.

Mouse controls
    
    Scroll wheel will control zoom.
    Right hand click and drag to pan.
    Right hand click only. Open a context menu for cut, copy and paste.

    Design Mode
        Left click on a tab to start a wire, left click on a tab to complete a wire.
        Left click on a tab to start a wire, left click on a wire to add a Junction.
        Right hand click for context menu (Cut,Copy,Paste)
        Right hand click and drag for pan.
        Left Click and Drag on component, wire, junction or pin to move.
        Left click on component to select it (properties panel will show component details).
    
    Simulation Mode
        Left Click on component to interact with it, push button etc.

Cut, Copy and Paste.

    Cut, copy and paste options on the menu. CTRL-C, CRTL-V Keyboard support
    Select All on the menu CRTL-A
    Bounding box selection. Clicking on Empty canvas starts selection.

Zoom
    User can zoom in and out. All components and wires will scale correctly.
    If fonts become too small when zoomed out very far they can be hidden, but will re-appear when zoomed back in.

Canvas Settings

    When switching pages the designer will remember the position of the canvas and current zoom level of each page.
    These parameters will be saved to the .rsim file.

Page ordering and renaming
    User will be able to re-order the page tabs and rename the pages in the document

Recent Documents
    An option should be included to clear recent documents
    If a user tries to open a recent document but it is not found, remove it from the list.





