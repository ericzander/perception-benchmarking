# perception-benchmarking
Robotic perception benchmarking with Isaac Sim, ROS2, and PyTorch with NVIDIA Brev

## Starting Instance and Streaming Isaac Sim

1. Use Brev launchable to start an instance
2. Once running, SSH with the Brev CLI, VS Code, etc
3. Ensure ports for streaming are open for your IP (49100, 47998)
4. Start Isaac Sim
    > $ bash infra/start-isaac.sh
5. Get the instance IP and start streaming with the [WebRTC client](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/manual_livestream_clients.html)
6. **When finished**: Stop Isaac Sim container
    > $ bash infra/stop-isaac.sh

## Testing Integration with ROS

1. Start the ROS2 container (Jazzy)
    > $ bash infra/start-ros.sh
2. **Optional**: Test Isaac Sim's internal ROS
    - Enable ROS2 bridge
    - Publish `/clock`
    - Verify
        > $ ros2 topic echo /clock
