class _M:
    def __init__(self, **kw):
        for k, v in self._d.items(): setattr(self, k, v() if callable(v) else v)
        self.__dict__.update(kw)
class OffboardControlMode(_M): _d = dict(position=False, velocity=False, acceleration=False, attitude=False, body_rate=False, timestamp=0)
class TrajectorySetpoint(_M): _d = dict(position=list, velocity=list, acceleration=list, yaw=0.0, timestamp=0)
class VehicleCommand(_M):
    _d = dict(command=0, param1=0., param2=0., param3=0., param4=0., param5=0., param6=0., param7=0., target_system=0, target_component=0, source_system=0, source_component=0, from_external=False, timestamp=0)
    VEHICLE_CMD_COMPONENT_ARM_DISARM = 400; VEHICLE_CMD_DO_SET_MODE = 176
    VEHICLE_CMD_NAV_LAND = 21; VEHICLE_CMD_NAV_RETURN_TO_LAUNCH = 20
class VehicleLocalPosition(_M): _d = dict(x=0., y=0., z=0., vx=0., vy=0., vz=0., heading=0., xy_valid=True, z_valid=True, xy_global=True, ref_lat=39.9208, ref_lon=32.8541)
class VehicleGlobalPosition(_M): _d = dict(lat=0., lon=0., alt=0.)
class VehicleStatus(_M):
    _d = dict(arming_state=1, nav_state=4)
    ARMING_STATE_ARMED = 2; NAVIGATION_STATE_OFFBOARD = 14
class BatteryStatus(_M): _d = dict(remaining=0.9)
class VehicleLandDetected(_M): _d = dict(landed=True)
