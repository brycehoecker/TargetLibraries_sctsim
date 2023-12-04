"""
Create an ASCII file containing the mapping for the "basic" scripts
"""
from target_calib import CameraConfiguration


def main():
    camera_version = "1.0.1"
    camera_config = CameraConfiguration(camera_version)
    m = camera_config.GetMapping()
    m.CreateASCII("full_camera_mapping.cfg")


if __name__ == '__main__':
    main()
