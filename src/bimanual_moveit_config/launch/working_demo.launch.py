import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("bimanual", package_name="bimanual_moveit_config")
        .to_moveit_configs()
    )

    # robot_description as a string param (the thing controller_manager needs)
    robot_description = {"robot_description": moveit_config.robot_description["robot_description"]}

    # robot_state_publisher - publishes /robot_description topic AND /tf
    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )

    # ros2_control_node - PASS robot_description directly as parameter (the fix!)
    ros2_controllers_path = os.path.join(
        FindPackageShare("bimanual_moveit_config").find("bimanual_moveit_config"),
        "config", "ros2_controllers.yaml",
    )
    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, ros2_controllers_path],
        output="both",
    )

    # move_group
    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
    )

    # RViz
    rviz_config = os.path.join(
        FindPackageShare("bimanual_moveit_config").find("bimanual_moveit_config"),
        "config", "moveit.rviz",
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
        ],
    )

    # Spawners
    def spawner(name):
        return Node(
            package="controller_manager",
            executable="spawner",
            arguments=[name, "--controller-manager", "/controller_manager"],
            output="screen",
        )

    return LaunchDescription([
        rsp,
        ros2_control_node,
        move_group,
        rviz,
        spawner("joint_state_broadcaster"),
        spawner("left_arm_controller"),
        spawner("right_arm_controller"),
        spawner("left_gripper_controller"),
    ])
