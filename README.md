# perception-benchmarking
Robotic perception benchmarking with Isaac Sim, ROS2, and PyTorch with NVIDIA Brev

## Project Description

1. Predict which direction is clear for traversal based on image perception
    * Live inference in Isaac Sim with PyTorch through ROS
2. Benchmark across varying conditions to test coverage and generalization
    * Lighting, obstacle appearance, obstacle layout, camera noise/blur/jitter, etc.
3. Compare different models
    * Simple, pretrained, fine-tuned

### Project Structure

There are two Docker containers at play: 
1. Isaac Sim
2. ROS 2 with Python (PyTorch, OpenCV, local installs, etc.)

ROS is bridged by using the host network and forcing FastDDS onto UDP.

## Running Isaac Sim and ROS

### Starting Instance and Streaming Isaac Sim

1. Use [Brev launchable](https://brev.nvidia.com/launchable/deploy?launchableID=env-3G6UsnO1yjIVDYFC52BdvNCawEH) to start an instance
2. Once running, SSH with the Brev CLI, VS Code, etc
3. Ensure ports for streaming are open for your IP (49100, 47998)
4. Start Isaac Sim
    > $ bash infra/start-isaac.sh
    - *Note that the shaders may take a few minutes to compile!*
5. Get the instance IP and start streaming with the [WebRTC client](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/manual_livestream_clients.html)
6. **When finished**: Stop Isaac Sim container
    > $ bash infra/stop-isaac.sh
    - *Or just terminate the instance*

### Testing Integration with ROS

1. Start the ROS2 container (Jazzy)
    > $ bash infra/start-ros.sh
2. Get a ROS2 shell
    > $ docker exec -it robot-benchmark-ros bash
3. **Optional**: Test Isaac Sim's internal ROS with clock
    - Ensure ROS2 bridge is enabled in extensions (should be on by default)
    - Publish `/clock` by creating the ROS2 action graph and playing
    - Verify in ROS2 shell
        > $ ros2 topic echo /clock

### Accessing Camera Data

1. Create a scene in Isaac Sim with a camera
2. Create a ROS2 action graph for the camera
3. WIP
