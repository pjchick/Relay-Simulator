"""
Example .rsim files for testing and documentation

This module contains example circuit definitions in .rsim format.
"""

# Example 1: Simple Switch and LED
SIMPLE_SWITCH_LED = """{
  "version": "1.0.0",
  "metadata": {
    "title": "Switch and LED",
    "author": "Relay Simulator",
    "description": "Simple test circuit with one switch controlling one LED",
    "created": "2025-12-10T10:00:00Z",
    "modified": "2025-12-10T10:00:00Z"
  },
  "pages": [
    {
      "page_id": "page0001",
      "name": "Main",
      "components": [
        {
          "component_id": "comp0001",
          "component_type": "Switch",
          "position": {"x": 100.0, "y": 100.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00001",
              "tabs": [
                {"tab_id": "tab00001", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00002", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00003", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00004", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "SW1",
            "label_position": "top",
            "mode": "toggle",
            "color": "red"
          }
        },
        {
          "component_id": "comp0002",
          "component_type": "Indicator",
          "position": {"x": 300.0, "y": 100.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00002",
              "tabs": [
                {"tab_id": "tab00005", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00006", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00007", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00008", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "LED1",
            "label_position": "top",
            "color": "green"
          }
        }
      ],
      "wires": [
        {
          "wire_id": "wire0001",
          "start_tab_id": "tab00002",
          "end_tab_id": "tab00008",
          "waypoints": [],
          "junctions": []
        }
      ]
    }
  ]
}"""

# Example 2: Switch, Relay, and LED
RELAY_CIRCUIT = """{
  "version": "1.0.0",
  "metadata": {
    "title": "Relay Circuit",
    "description": "Switch controls relay which controls LED"
  },
  "pages": [
    {
      "page_id": "page0001",
      "name": "Main",
      "components": [
        {
          "component_id": "sw000001",
          "component_type": "Switch",
          "position": {"x": 50.0, "y": 100.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00001",
              "tabs": [
                {"tab_id": "tab00001", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00002", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00003", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00004", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "SW1",
            "mode": "toggle",
            "color": "red"
          }
        },
        {
          "component_id": "vcc00001",
          "component_type": "VCC",
          "position": {"x": 50.0, "y": 50.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00002",
              "tabs": [
                {"tab_id": "tab00005", "position": {"x": 0.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {}
        },
        {
          "component_id": "rly00001",
          "component_type": "DPDTRelay",
          "position": {"x": 200.0, "y": 100.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00003",
              "tabs": [
                {"tab_id": "tab00006", "position": {"x": -30.0, "y": -40.0}}
              ]
            },
            {
              "pin_id": "pin00004",
              "tabs": [
                {"tab_id": "tab00007", "position": {"x": -10.0, "y": 40.0}}
              ]
            },
            {
              "pin_id": "pin00005",
              "tabs": [
                {"tab_id": "tab00008", "position": {"x": 0.0, "y": 40.0}}
              ]
            },
            {
              "pin_id": "pin00006",
              "tabs": [
                {"tab_id": "tab00009", "position": {"x": 10.0, "y": 40.0}}
              ]
            },
            {
              "pin_id": "pin00007",
              "tabs": [
                {"tab_id": "tab00010", "position": {"x": 20.0, "y": 40.0}}
              ]
            },
            {
              "pin_id": "pin00008",
              "tabs": [
                {"tab_id": "tab00011", "position": {"x": 30.0, "y": 40.0}}
              ]
            },
            {
              "pin_id": "pin00009",
              "tabs": [
                {"tab_id": "tab00012", "position": {"x": 40.0, "y": 40.0}}
              ]
            }
          ],
          "properties": {
            "label": "K1",
            "color": "blue"
          }
        },
        {
          "component_id": "led00001",
          "component_type": "Indicator",
          "position": {"x": 350.0, "y": 100.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00010",
              "tabs": [
                {"tab_id": "tab00013", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00014", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00015", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00016", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "LED1",
            "color": "green"
          }
        }
      ],
      "wires": [
        {
          "wire_id": "wire0001",
          "start_tab_id": "tab00005",
          "end_tab_id": "tab00006",
          "waypoints": []
        },
        {
          "wire_id": "wire0002",
          "start_tab_id": "tab00002",
          "end_tab_id": "tab00007",
          "waypoints": []
        },
        {
          "wire_id": "wire0003",
          "start_tab_id": "tab00009",
          "end_tab_id": "tab00016",
          "waypoints": []
        }
      ]
    }
  ]
}"""

# Example 3: Cross-Page Links
CROSS_PAGE_LINKS = """{
  "version": "1.0.0",
  "metadata": {
    "title": "Cross-Page Links Example",
    "description": "Demonstrates link connections between pages"
  },
  "pages": [
    {
      "page_id": "page0001",
      "name": "Input Page",
      "components": [
        {
          "component_id": "sw000001",
          "component_type": "Switch",
          "position": {"x": 100.0, "y": 100.0},
          "rotation": 0,
          "link_name": "SIGNAL_A",
          "pins": [
            {
              "pin_id": "pin00001",
              "tabs": [
                {"tab_id": "tab00001", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00002", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00003", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00004", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "Input A",
            "mode": "toggle",
            "color": "red"
          }
        },
        {
          "component_id": "sw000002",
          "component_type": "Switch",
          "position": {"x": 100.0, "y": 200.0},
          "rotation": 0,
          "link_name": "SIGNAL_B",
          "pins": [
            {
              "pin_id": "pin00002",
              "tabs": [
                {"tab_id": "tab00005", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00006", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00007", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00008", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "Input B",
            "mode": "toggle",
            "color": "blue"
          }
        }
      ],
      "wires": []
    },
    {
      "page_id": "page0002",
      "name": "Output Page",
      "components": [
        {
          "component_id": "led00001",
          "component_type": "Indicator",
          "position": {"x": 100.0, "y": 100.0},
          "rotation": 0,
          "link_name": "SIGNAL_A",
          "pins": [
            {
              "pin_id": "pin00003",
              "tabs": [
                {"tab_id": "tab00009", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00010", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00011", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00012", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "Output A",
            "color": "green"
          }
        },
        {
          "component_id": "led00002",
          "component_type": "Indicator",
          "position": {"x": 100.0, "y": 200.0},
          "rotation": 0,
          "link_name": "SIGNAL_B",
          "pins": [
            {
              "pin_id": "pin00004",
              "tabs": [
                {"tab_id": "tab00013", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00014", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00015", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00016", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "Output B",
            "color": "yellow"
          }
        }
      ],
      "wires": []
    }
  ]
}"""

# Example 4: Wire with Junction
WIRE_WITH_JUNCTION = """{
  "version": "1.0.0",
  "metadata": {
    "title": "Junction Example",
    "description": "Wire with junction branching to multiple tabs"
  },
  "pages": [
    {
      "page_id": "page0001",
      "name": "Main",
      "components": [
        {
          "component_id": "sw000001",
          "component_type": "Switch",
          "position": {"x": 100.0, "y": 150.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00001",
              "tabs": [
                {"tab_id": "tab00001", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00002", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00003", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00004", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "SW1",
            "mode": "toggle"
          }
        },
        {
          "component_id": "led00001",
          "component_type": "Indicator",
          "position": {"x": 300.0, "y": 100.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00002",
              "tabs": [
                {"tab_id": "tab00005", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {"label": "LED1"}
        },
        {
          "component_id": "led00002",
          "component_type": "Indicator",
          "position": {"x": 300.0, "y": 150.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00003",
              "tabs": [
                {"tab_id": "tab00006", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {"label": "LED2"}
        },
        {
          "component_id": "led00003",
          "component_type": "Indicator",
          "position": {"x": 300.0, "y": 200.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00004",
              "tabs": [
                {"tab_id": "tab00007", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {"label": "LED3"}
        }
      ],
      "wires": [
        {
          "wire_id": "wire0001",
          "start_tab_id": "tab00002",
          "end_tab_id": null,
          "waypoints": [
            {"waypoint_id": "wp000001", "position": {"x": 150.0, "y": 150.0}}
          ],
          "junctions": [
            {
              "junction_id": "junc0001",
              "position": {"x": 200.0, "y": 150.0},
              "child_wires": [
                {
                  "wire_id": "wire0002",
                  "start_tab_id": "junc0001",
                  "end_tab_id": "tab00005",
                  "waypoints": []
                },
                {
                  "wire_id": "wire0003",
                  "start_tab_id": "junc0001",
                  "end_tab_id": "tab00006",
                  "waypoints": []
                },
                {
                  "wire_id": "wire0004",
                  "start_tab_id": "junc0001",
                  "end_tab_id": "tab00007",
                  "waypoints": []
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}"""

# Example 5: Complex Circuit (Multiple Relays)
COMPLEX_CIRCUIT = """{
  "version": "1.0.0",
  "metadata": {
    "title": "Complex Relay Circuit",
    "description": "Multiple relays with interlocking logic",
    "author": "Relay Simulator"
  },
  "pages": [
    {
      "page_id": "page0001",
      "name": "Control Logic",
      "components": [
        {
          "component_id": "vcc00001",
          "component_type": "VCC",
          "position": {"x": 50.0, "y": 50.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00001",
              "tabs": [
                {"tab_id": "tab00001", "position": {"x": 0.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {}
        },
        {
          "component_id": "sw000001",
          "component_type": "Switch",
          "position": {"x": 100.0, "y": 100.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00002",
              "tabs": [
                {"tab_id": "tab00002", "position": {"x": 20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {"label": "Start", "mode": "pushbutton"}
        },
        {
          "component_id": "sw000002",
          "component_type": "Switch",
          "position": {"x": 100.0, "y": 150.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00003",
              "tabs": [
                {"tab_id": "tab00003", "position": {"x": 20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {"label": "Stop", "mode": "pushbutton"}
        },
        {
          "component_id": "rly00001",
          "component_type": "DPDTRelay",
          "position": {"x": 250.0, "y": 100.0},
          "rotation": 0,
          "pins": [
            {"pin_id": "pin00004", "tabs": [{"tab_id": "tab00004", "position": {"x": -30.0, "y": -40.0}}]},
            {"pin_id": "pin00005", "tabs": [{"tab_id": "tab00005", "position": {"x": -10.0, "y": 40.0}}]},
            {"pin_id": "pin00006", "tabs": [{"tab_id": "tab00006", "position": {"x": 0.0, "y": 40.0}}]},
            {"pin_id": "pin00007", "tabs": [{"tab_id": "tab00007", "position": {"x": 10.0, "y": 40.0}}]},
            {"pin_id": "pin00008", "tabs": [{"tab_id": "tab00008", "position": {"x": 20.0, "y": 40.0}}]},
            {"pin_id": "pin00009", "tabs": [{"tab_id": "tab00009", "position": {"x": 30.0, "y": 40.0}}]},
            {"pin_id": "pin00010", "tabs": [{"tab_id": "tab00010", "position": {"x": 40.0, "y": 40.0}}]}
          ],
          "properties": {"label": "K1"}
        },
        {
          "component_id": "led00001",
          "component_type": "Indicator",
          "position": {"x": 400.0, "y": 100.0},
          "rotation": 0,
          "link_name": "RUN_INDICATOR",
          "pins": [
            {
              "pin_id": "pin00011",
              "tabs": [
                {"tab_id": "tab00011", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {"label": "Run", "color": "green"}
        }
      ],
      "wires": [
        {"wire_id": "wire0001", "start_tab_id": "tab00001", "end_tab_id": "tab00004"},
        {"wire_id": "wire0002", "start_tab_id": "tab00002", "end_tab_id": "tab00005"},
        {"wire_id": "wire0003", "start_tab_id": "tab00007", "end_tab_id": "tab00011"}
      ]
    }
  ]
}"""

# Invalid examples for testing error handling
INVALID_VERSION = """{
  "version": "99.0.0",
  "pages": [
    {
      "page_id": "page001",
      "name": "Test"
    }
  ]
}"""

INVALID_MISSING_REQUIRED = """{
  "version": "1.0.0",
  "pages": [
    {
      "name": "Test"
    }
  ]
}"""

INVALID_ID_FORMAT = """{
  "version": "1.0.0",
  "pages": [
    {
      "page_id": "INVALID_ID_TOO_LONG",
      "name": "Test",
      "components": []
    }
  ]
}"""

INVALID_ROTATION = """{
  "version": "1.0.0",
  "pages": [
    {
      "page_id": "page0001",
      "name": "Test",
      "components": [
        {
          "component_id": "comp0001",
          "component_type": "Switch",
          "position": {"x": 0.0, "y": 0.0},
          "rotation": 45,
          "pins": []
        }
      ]
    }
  ]
}"""
