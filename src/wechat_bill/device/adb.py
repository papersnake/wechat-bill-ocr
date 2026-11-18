from __future__ import annotations

import io
from typing import Optional, Tuple

from adbutils import AdbClient, AdbDevice, adb
from loguru import logger
from PIL import Image


class DeviceController:
    """封装 adbutils，提供截图与滑动。"""

    def __init__(
        self,
        serial: Optional[str] = None,
        host: str = "127.0.0.1",
        port: int = 5037,
    ):
        self.client = AdbClient(host=host, port=port)
        self.device: AdbDevice = self._select_device(serial)
        logger.info("已连接设备: {}", self.device.serial)

    def _select_device(self, preferred: Optional[str]) -> AdbDevice:
        devices = self.client.device_list()
        if not devices:
            raise RuntimeError(
                "没有检测到任何 adb 设备。请确认手机已开启 USB/无线调试并已连接。"
            )

        if preferred:
            for d in devices:
                if d.serial == preferred:
                    return self.client.device(preferred)
            logger.warning("指定设备 {} 不在线，将使用第一个可用设备", preferred)

        if len(devices) > 1:
            logger.info("检测到多个设备，自动选择第一个: {}", devices[0].serial)
            for i, d in enumerate(devices, 1):
                logger.info("  {}. {}", i, d.serial)

        return self.client.device(devices[0].serial)

    def screen_size(self) -> Tuple[int, int]:
        w, h = self.device.window_size()
        return int(w), int(h)

    def screenshot(self) -> Image.Image:
        """返回 PIL Image。"""
        return self.device.screenshot()

    def screenshot_bytes(self) -> bytes:
        img = self.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def swipe_up(self, screen_height: Optional[int] = None, duration_ms: int = 350):
        w, h = self.screen_size()
        if screen_height:
            h = screen_height
        x = w // 2
        y_start = int(h * 0.72)
        y_end = int(h * 0.32)
        # adbutils swipe duration 单位是秒
        self.device.swipe(x, y_start, x, y_end, duration_ms / 1000.0)

    def shell(self, cmd: str) -> str:
        return self.device.shell(cmd)
