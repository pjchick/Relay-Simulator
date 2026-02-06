I want to explore the possibility of sub circuits.

An example sub circuit file is D:\repos\Relay-Simulator\examples\Latch.rsub

I want to be able to load a sub curcuit and then use it as a component. I want to be able to drag it onto the canvas and connect wires to it.

Every time I drag a sub circuit onto the canvas a new instance of that sub circuit will be created. Every instance of a sub circuit is unique.

Once a sub circuit is added to a document a copy of the sub circuit will be added to the main .rsim document. The .rsub file will act as a template.

Valid Sub-circuit file MUST have a page called 'FOOTPRINT'. This is what will be shown on the canvas.

The footprint will have LINKS placed on it. These will then act as pins from the main circuit to the instance of the sub_circuit.

When the simulator is running all the logic on the other pages of the sub-circuit will be processed in the normal way.

