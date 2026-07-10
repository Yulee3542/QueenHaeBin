"""autodrive_skku 전체 노드 + foxglove_bridge 기동.

사용 예:
  ros2 launch autodrive_skku_ros bringup.launch.py mission:=road foxglove_port:=8765

mission 인자는 필수로 지정할 것 — ROS 2 launch 시스템은 자식 프로세스의 stdin을
연결하지 않는 알려진 제약(ros2/launch#735)이 있어 mission_node의 대화형 메뉴가
여기서는 동작하지 않는다(생략하면 mission_node가 에러 메시지를 내고 즉시 종료).
대화형 메뉴가 필요하면 'ros2 run autodrive_skku_ros mission_node'로 직접 실행할 것.

arduino_port/lidar_port를 생략하면 시리얼 포트를 자동 감지한다(기존
tools/ports.py의 autodetect_ports()를 launch 생성 시점에 그대로 재사용).
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

from autodrive_skku_ros.nodes.ports import autodetect_ports


def generate_launch_description():
    auto_arduino, auto_lidar = autodetect_ports()

    mission_arg = DeclareLaunchArgument(
        "mission",  # default_value 없음 = 필수 인자, 생략 시 노드 기동 전에 바로 에러
        description="road|traffic|t_parking (필수 — 대화형 메뉴는 ros2 launch에서 안 됨)")
    arduino_port_arg = DeclareLaunchArgument(
        "arduino_port", default_value=auto_arduino or "",
        description="아두이노 시리얼 포트 (예: /dev/ttyACM0)")
    lidar_port_arg = DeclareLaunchArgument(
        "lidar_port", default_value=auto_lidar or "/dev/ttyUSB0",
        description="라이다 시리얼 포트")
    front_camera_arg = DeclareLaunchArgument("front_camera", default_value="0")
    rear_camera_arg = DeclareLaunchArgument(
        "rear_camera", default_value="-1", description="-1이면 후방 카메라 미사용")
    show_arg = DeclareLaunchArgument(
        "show", default_value="false", description="카메라 창 표시 (디스플레이 필요)")
    foxglove_port_arg = DeclareLaunchArgument("foxglove_port", default_value="8765")

    arduino_bridge = Node(
        package="autodrive_skku_ros",
        executable="arduino_bridge_node",
        parameters=[{"port": LaunchConfiguration("arduino_port")}],
    )

    camera_publisher = Node(
        package="autodrive_skku_ros",
        executable="camera_publisher_node",
        parameters=[{
            "front_camera_index": ParameterValue(LaunchConfiguration("front_camera"), value_type=int),
            "rear_camera_index": ParameterValue(LaunchConfiguration("rear_camera"), value_type=int),
        }],
    )

    rplidar = Node(
        package="rplidar_ros",
        executable="rplidar_composition",
        parameters=[{
            "serial_port": LaunchConfiguration("lidar_port"),
            "serial_baudrate": 115200,
            "frame_id": "laser",
            "angle_compensate": True,
        }],
    )

    lidar_geometry = Node(
        package="autodrive_skku_ros",
        executable="lidar_geometry_node",
    )

    mission = Node(
        package="autodrive_skku_ros",
        executable="mission_node",
        parameters=[{
            "mission": LaunchConfiguration("mission"),
            "show": ParameterValue(LaunchConfiguration("show"), value_type=bool),
        }],
        output="screen",
        emulate_tty=True,
    )

    foxglove_bridge = Node(
        package="foxglove_bridge",
        executable="foxglove_bridge",
        parameters=[{
            "port": ParameterValue(LaunchConfiguration("foxglove_port"), value_type=int),
        }],
    )

    return LaunchDescription([
        mission_arg, arduino_port_arg, lidar_port_arg,
        front_camera_arg, rear_camera_arg, show_arg, foxglove_port_arg,
        arduino_bridge, camera_publisher, rplidar, lidar_geometry, mission, foxglove_bridge,
    ])
