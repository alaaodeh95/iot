Homework Assignment: Smart Home IoT Simulation

Objective:
This assignment will help you understand the basic principles of IoT systems through simulation. You will model a simple Smart Home environment with sensors, a central computer (controller), and actuators.

Scenario:
Imagine a smart home equipped with various IoT devices:

Sensors: Devices that sense the environment (e.g., temperature, light, motion, humidity, gas).
Central Computer (Controller): Collects sensor data, analyzes it, and makes decisions.
Actuators: Devices that execute commands (e.g., turn on/off lights, fans, alarms, or sprinklers).
The simulation should generate random sensor data (within realistic ranges) and demonstrate how the central computer makes decisions based on this data, then sends corresponding commands to actuators.

Requirements:

Sensors

Simulate at least 3 types of sensors (e.g., temperature, motion, light).
Each sensor should periodically generate random values.
Example ranges:

Temperature: 15–40 °C
Light: 0–100 (0 = dark, 100 = bright)
Motion: 0 (no motion) or 1 (motion detected)
Central Computer (Controller)

Collects all incoming sensor readings.
Implements decision-making rules (e.g., If temperature > 30, turn on fan; If motion detected and light < 20, turn on light).
Outputs log messages to the console (e.g., “Temperature = 35 → Fan ON”).
Actuators

Simulate at least 2 actuators (e.g., fan, light, alarm).
The central computer controls them based on sensor input.
Display actuator status (ON/OFF).
Simulation

Run for a fixed period (e.g., 20 cycles).
In each cycle: sensors send data → central computer analyzes → actuators respond.
Implementation Notes:

You may use Python, Java, or C++ for implementation.
Make your code modular (separate classes for sensors, controller, actuators).
Clearly print sensor readings, decisions, and actuator states at each step.

Add the following to the main project:

Since we have a set of sensors that send data to the main server, make one of these sensors send the data to a program that sends the data to the main server. That is, this new program represents a tier between the sensor and the main server (Gateway to filter outliers).

With respect to the main project:

Implemet both JSON and SOAP (XML format) to simulate sending data for both data representations and protocols.

1- JSON: choose one of the sensors to send data using JSON format (for example a sensor that measures temperature, humedity and pressure. The sensor could be located on the roof of the house). These data are stored in a JSON format and sent as pairs of data to the main server).

2- XML: Suppose the smart home has a dust cleaner that has a sensor and a camera that used to detect objects in a room. The sensor sends the main server the data: object distance, object name (after an image processing program recognized the object), and the strength of detection signal used by the cleaner. All data (text) sent to the main server using XML format.

Objective:
Following what you have developed in the first phase, the objective of this phase is
involve data analytics for the data collected from the sensors in the developed IoT
system. Furthermore, a proper Machine Learning (ML) model should be built and
modified whenever needed. This ML model should guide the application control to
make proper decisions (instead of having just rule-based decisions).
Requirements:
1. Modify the system you have implemented in phase#1 to perform the following:
a. Include additional types of sensors (in the attached document).
b. Designate one of the sensors to do initial filtration/processing before the
data reaches the gateway. That is, this sensor represents a tier between the sensors
and the gateway which, in turn, should send the data to the cloud.
c. Write a program to convert the data stored in the data warehouse into a form
that is ready to be further analyzed with descriptive analysis (Spreadsheet, visualized
form, etc,.. )
d. Perform proper prescriptive analysis to the data based on the resultant
descriptive analysis. Build a Machine Learning (ML) model for your system based on
the data. Be careful that this model should be modified whenever needed.
e. Use the built ML model to help the control application making proper
decisions so that proper commands are sent to the actuators (Prescriptive analysis).


For sensors:
check
./sensors.pdf
./sensors-sample data.pdf